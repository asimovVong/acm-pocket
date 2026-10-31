"""Standard-stream adapter used inside the browser's Python runtime."""

import builtins
import io
import json
import sys
import traceback


class OutputLimitError(Exception):
    pass


class CappedBuffer(io.BytesIO):
    def __init__(self, limit):
        super().__init__()
        self.limit = limit

    def write(self, data):
        remaining = max(0, self.limit - self.tell())
        if len(data) > remaining or self.tell() > self.limit:
            super().write(data[:remaining])
            raise OutputLimitError(f"输出超过本次运行的 {self.limit // 1024} KiB 上限。请缩小测试数据，或下载代码后在本机运行。")
        return super().write(data)


def execute_code(code, input_text, output_limit=65536):
    """Run a complete ACM program with fresh globals and captured UTF-8 streams."""
    stdin = io.TextIOWrapper(io.BytesIO(input_text.encode("utf-8")), encoding="utf-8")
    output_limit = min(8 * 1024 * 1024, max(1024, int(output_limit)))
    out_buffer, err_buffer = CappedBuffer(output_limit), CappedBuffer(output_limit)
    stdout = io.TextIOWrapper(out_buffer, encoding="utf-8", write_through=True)
    stderr = io.TextIOWrapper(err_buffer, encoding="utf-8", write_through=True)
    previous = sys.stdin, sys.stdout, sys.stderr, sys.argv
    error = None
    try:
        sys.stdin, sys.stdout, sys.stderr, sys.argv = stdin, stdout, stderr, ["main.py"]
        namespace = {"__name__": "__main__", "__file__": "main.py", "__builtins__": dict(vars(builtins))}
        exec(compile(code, "main.py", "exec"), namespace)
    except SystemExit as exc:
        if exc.code is not None and exc.code != 0:
            error = "SystemExit: " + str(exc.code)
    except BaseException:
        error = traceback.format_exc(limit=8)
    finally:
        sys.stdin, sys.stdout, sys.stderr, sys.argv = previous
    return {
        "stdout": out_buffer.getvalue().decode("utf-8", errors="replace"),
        "stderr": err_buffer.getvalue().decode("utf-8", errors="replace"),
        "error": error,
    }


def execute_code_json(code, input_text, output_limit=65536):
    return json.dumps(execute_code(code, input_text, output_limit), ensure_ascii=False)
