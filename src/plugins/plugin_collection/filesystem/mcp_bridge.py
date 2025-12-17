import asyncio
import json
import os
import sys


class AsyncMCPBridge:
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None
        self.lock = asyncio.Lock()
        self._msg_id = 0

    def _get_next_id(self):
        self._msg_id += 1
        return self._msg_id

    async def start(self):
        if self.process: return
        print(f"🔄 [MCP] 正在启动进程: {' '.join(self.cmd)}")
        self.process = await asyncio.create_subprocess_exec(
            *self.cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            # 握手流程
            init_id = self._get_next_id()
            await self._send_json({
                "jsonrpc": "2.0", "id": init_id, "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "mmcp-wrapper", "version": "1.0"}
                }
            })

            while True:
                resp = await self._read_json()
                if resp.get("id") == init_id: break

            await self._send_json({
                "jsonrpc": "2.0", "method": "notifications/initialized"
            })
            print("✅ [MCP] 握手完成")
        except Exception as e:
            if self.process: self.process.kill()
            self.process = None
            raise e

    async def _send_json(self, data):
        if not self.process: return
        self.process.stdin.write((json.dumps(data) + "\n").encode("utf-8"))
        await self.process.stdin.drain()

    async def _read_json(self):
        line = await self.process.stdout.readline()
        if not line: raise EOFError("MCP Server closed connection")
        return json.loads(line.decode("utf-8"))

    async def call_tool(self, name: str, args: dict):
        if not self.process: await self.start()
        async with self.lock:
            req_id = self._get_next_id()
            await self._send_json({
                "jsonrpc": "2.0", "id": req_id, "method": "tools/call",
                "params": {"name": name, "arguments": args}
            })

            while True:
                resp = await self._read_json()
                if resp.get("id") == req_id:
                    return self._parse_result(resp)

    def _parse_result(self, resp: dict):
        if "error" in resp:
            return f"Error {resp['error'].get('code')}: {resp['error'].get('message')}"

        result = resp.get("result", {})
        content = result.get("content", [])

        # 增强解析：处理文本和图片/多媒体
        output_parts = []
        for item in content:
            if item.get("type") == "text":
                output_parts.append(item.get("text", ""))
            elif item.get("type") in ["image", "resource"]:
                # 对于图片或二进制，返回摘要信息或Base64片段
                data = item.get("data", "") or item.get("blob", "")
                mime = item.get("mimeType", "unknown")
                output_parts.append(f"[Media: {mime}, size={len(data)} chars]")
            else:
                output_parts.append(f"[{item.get('type')} content]")

        return "\n".join(output_parts) if output_parts else "Success (No output)"


_bridge_instance = None


def get_bridge():
    global _bridge_instance
    if _bridge_instance is None:
        allowed_path = os.path.abspath(os.getcwd())
        is_windows = sys.platform.startswith('win')
        npx_cmd = "npx.cmd" if is_windows else "npx"
        # 关键：加上 -y 自动安装，传入 allowed_path
        cmd = [npx_cmd, "-y", "@modelcontextprotocol/server-filesystem", allowed_path]
        _bridge_instance = AsyncMCPBridge(cmd)
    return _bridge_instance