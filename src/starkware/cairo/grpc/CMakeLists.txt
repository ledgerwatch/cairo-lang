python_lib(cairo_grpc_lib
    PREFIX starkware/cairo/grpc
    FILES
    __init__.py
    cairo_pb2.py
    cairo_pb2_grpc.py
    methods.py
    helper.py
    server.py
)
full_python_test(cairo_grpc_test
    PREFIX starkware/cairo/grpc
    PYTHON python3.7
    TESTED_MODULES starkware/cairo/grpc

    FILES
    methods_test.py
    test.cairo
    test_contract.cairo

    LIBS
    cairo_common_lib
    cairo_compile_lib
    cairo_grpc_lib
    starknet_cli_lib
    starknet_testing_lib
    pip_pytest
    pip_pytest_asyncio
)