from google.protobuf.any_pb2 import Any
from google.protobuf.wrappers_pb2 import StringValue, Int32Value
from typing import List
import binascii

from starkware.starknet.cli.starknet_cli import get_gateway_client, get_feeder_gateway_client
from starkware.starkware_utils.error_handling import StarkErrorCode


class InvokeParams:
    inputs: List[str] = []
    address: str = ""
    function: str = ""
    code: str = ""
    block_hash: str = None
    block_number: int = None
    gateway_url: str = None
    feeder_gateway_url: str = None
    network: str = "alpha-goerli"
    command: str = "invoke"
    testing = False

    def __init__(self, data: {}):
        for key in data:
            if key == "inputs":
                if (len(data[key]) != 0):
                    self.__setattr__(key, data[key].split(","))
            elif key == "code":
                if (len(data[key]) != 0):
                    self.__setattr__(key, binascii.unhexlify(data[key].replace("0x", "") if data[key].startswith("0x") else data[key]))
            elif hasattr(self, key):
                if (key == "testing"):
                    self.__setattr__(key, data[key])
                elif (len(data[key]) != 0):
                    self.__setattr__(key, data[key])


class MockGateway:
    CALL_RESULT = 1
    INVOKE_RESULT = 2

    async def call_contract(self, invoke_tx, block_hash, block_number):
        return {"result": self.CALL_RESULT}

    async def add_transaction(self, tx):
        return {"code": StarkErrorCode.TRANSACTION_RECEIVED.name, "transaction_hash": self.INVOKE_RESULT}


def get_feeder_gateway_client_wrapper(params: InvokeParams):
    if params.testing:
        return MockGateway()
    else:
        return get_feeder_gateway_client(params)


def get_gateway_client_wrapper(params: InvokeParams):
    if params.testing:
        return MockGateway()
    else:
        return get_gateway_client(params)


def encode_grpc_any_array(arr: []) -> []:
    result = []
    for value in arr:
        packaged_value = Any()
        if isinstance(value, int):
            packaged_value.Pack(Int32Value(value=value))
        else:
            packaged_value.Pack(StringValue(value=value))

        result.append(packaged_value)

    return result


def encode_grpc_any_map(arr: {}) -> {}:
    result = {}
    for key in arr:
        packaged_value = Any()
        if isinstance(arr[key], int):
            packaged_value.Pack(Int32Value(value=arr[key]))
        else:
            packaged_value.Pack(StringValue(value=arr[key]))

        result[key] = packaged_value

    return result


def decode_grpc_any_array(arr: []) -> []:
    result = []
    for value in arr:
        if value.Is(Int32Value.DESCRIPTOR):
            v = Int32Value()
        else:
            v = StringValue()

        if value.Unpack(v):
            result.append(v.value)

    return result


def decode_grpc_any_map(arr: {}) -> {}:
    result = {}
    for key in arr:
        if arr[key].Is(Int32Value.DESCRIPTOR):
            v = Int32Value()
        else:
            v = StringValue()

        if arr[key].Unpack(v):
            result[key] = v.value

    return result
