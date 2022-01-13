import pytest
import os
import re
import binascii

from starkware.cairo.grpc.methods import call_cairo_run, call_starknet_run
from starkware.cairo.grpc.helper import MockGateway
from starkware.cairo.lang.cairo_constants import DEFAULT_PRIME
from starkware.cairo.lang.compiler.cairo_compile import compile_cairo_files
from starkware.cairo.lang.vm.vm_exceptions import VmException

CODE_FILE = os.path.join(os.path.dirname(__file__), "test.cairo")
CONTRACT_FILE = os.path.join(os.path.dirname(__file__), "test_contract.cairo")

from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.testing.starknet import Starknet

@pytest.fixture
async def starknet() -> Starknet:
    return await Starknet.empty()


@pytest.fixture
async def contract(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(source=CONTRACT_FILE)


@pytest.mark.asyncio
async def test_cairo_call():
    number = 25
    code_definition = compile_cairo_files([CODE_FILE], debug_info=True, prime=DEFAULT_PRIME)
    code = code_definition.serialize()
    params = {"input": number, "function": "double"}

    code = binascii.hexlify(code)

    result = call_cairo_run(params, code)
    assert len(result) == 1
    assert result[0] == number * 2

    params = {"input": number, "function": "pow"}
    result = call_cairo_run(params, code)
    assert len(result) == 1
    assert result[0] == number * number

    params = {"input": number, "function": "unknown"}
    result = call_cairo_run(params, code)
    assert len(result) == 1
    assert result[0] == number

    params = {"function": "pow"}
    with pytest.raises(
        VmException, match=re.escape("KeyError: 'input'")
    ):
        call_cairo_run(params, code)


@pytest.mark.asyncio
async def test_starknet_call(contract: StarknetContract):
    paramsDict = {
        "address": hex(contract.contract_address),
        "function": "get_balance",
        "testing": True
    }

    result = await call_starknet_run(paramsDict)
    assert len(result) == 1
    assert result[0] == MockGateway.CALL_RESULT

@pytest.mark.asyncio
async def test_starknet_address_error(contract: StarknetContract):
    paramsDict = {
        "address": "123123",
        "function": "get_balance",
        "inputs": "1234",
        "testing": True
    }
    with pytest.raises(
        AssertionError, match=re.escape("The address must start with '0x'")
    ):
        await call_starknet_run(paramsDict)
