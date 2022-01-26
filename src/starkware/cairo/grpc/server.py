import grpc
import sys
import os
import argparse
import asyncio
from threading import Thread
from concurrent import futures

from starkware.cairo.grpc.helper import encode_grpc_any_array, decode_grpc_any_map
from starkware.cairo.grpc import cairo_pb2, cairo_pb2_grpc
from starkware.cairo.grpc.methods import call_cairo_run, call_starknet_run

class CairoServicer(cairo_pb2_grpc.CAIROVMServicer):

    def Call(self, request, context):
        params = decode_grpc_any_map(request.params)
        method = request.method

        try:
            if method == "cairo_run":
                result = call_cairo_run(params, request.code)
            elif method == "starknet_call":
                result = asyncio.run(call_starknet_run(params))
            else:
                result = ["Error. Unknown method: " + method]
        except Exception as exc:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            result = ["Error: " + str(exc), "File: " + fname, "Line " + str(exc_tb.tb_lineno)]

        response = cairo_pb2.CallResponse()
        response.result.extend(encode_grpc_any_array(result))

        return response


def start_server(port: int, host: str):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    cairo_pb2_grpc.add_CAIROVMServicer_to_server(CairoServicer(), server)
    server.add_insecure_port(f"{host}:{port}")

    server.start()
    server.wait_for_termination()

def main():
    parser = argparse.ArgumentParser(description="Run Cairo grpc server.")
    parser.add_argument(
        "--port",
        type=int,
        help="Port ro run grpc server",
        default=6066
    )
    parser.add_argument(
        "--host",
        type=str,
        help="Host address ro run grpc server",
        default="[::]"
    )

    parser.add_argument(
        "-d",
        "--daemon",
        help="Host address ro run grpc server",
        action="store_true"
    )

    args = parser.parse_args()

    print(f"Starting server on port {args.port}.")

    if args.daemon:
        ## TODO: move daemon to file
        t = Thread(target=start_server, args=(args.port, args.host), daemon=True)
        t.start()
    else:
        start_server(args.port, args.host)


if __name__ == '__main__':
    sys.exit(main())