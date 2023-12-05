# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 philanthrope

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import Crypto
import typing
import pydantic
import bittensor as bt

from Crypto.PublicKey import ECC


# Basically setup for a given piece of data
class Store(bt.Synapse):
    # Data to store
    encrypted_data: str  # base64 encoded string of encrypted data (bytes)

    # Setup parameters
    curve: str  # e.g. P-256
    g: str  # base point   (hex string representation)
    h: str  # random point (hex string representation)

    seed: typing.Union[
        str, int, bytes
    ]  # random seed (bytes stored as hex) for the commitment

    # Return signature of received data
    randomness: typing.Optional[int] = None
    commitment: typing.Optional[str] = None
    signature: typing.Optional[bytes] = None
    commitment_hash: typing.Optional[str] = None  # includes seed

    required_hash_fields: typing.List[str] = pydantic.Field(
        [
            "curve",
            "g",
            "h",
            "seed",
            "randomness",
            "commitment",
            "signature",
            "commitment_hash",
        ],
        title="Required Hash Fields",
        description="A list of required fields for the hash.",
        allow_mutation=False,
    )

    def __str__(self):
        return (
            f"Store(encrypted_data={self.encrypted_data[:32]}, "
            f"curve={self.curve}, "
            f"g={self.g}, "
            f"h={self.h}, "
            f"seed={self.seed}, "
            f"randomness={self.randomness}, "
            f"commitment={self.commitment}, "
            f"signature={self.signature}, "
            f"commitment_hash={self.commitment_hash})"
            f"axon={self.axon.dict()}, "
            f"dendrite={self.dendrite.dict()}"
        )


class StreamStore(bt.StreamingSynapse):
    # Data to store
    encrypted_data: str  # base64 encoded string of encrypted data (bytes)

    # Setup parameters
    curve: str  # e.g. P-256
    g: str  # base point   (hex string representation)
    h: str  # random point (hex string representation)

    seed: typing.Union[
        str, int, bytes
    ]  # random seed (bytes stored as hex) for the commitment

    # Return signature of received data
    randomness: typing.Optional[int] = None
    commitment: typing.Optional[str] = None
    signature: typing.Optional[bytes] = None
    commitment_hash: typing.Optional[str] = None  # includes seed

    required_hash_fields: typing.List[str] = pydantic.Field(
        [
            "curve",
            "g",
            "h",
            "seed",
            "randomness",
            "commitment",
            "signature",
            "commitment_hash",
        ],
        title="Required Hash Fields",
        description="A list of required fields for the hash.",
        allow_mutation=False,
    )

    async def process_streaming_response(self, response: StreamingResponse):
        async for chunk in response.content.iter_any():
            yield chunk

    def extract_response_json(self, response: StreamingResponse) -> dict:
        headers = {
            k.decode("utf-8"): v.decode("utf-8")
            for k, v in response.__dict__["_raw_headers"]
        }

        def extract_info(prefix):
            return {
                key.split("_")[-1]: value
                for key, value in headers.items()
                if key.startswith(prefix)
            }

        return {
            "name": headers.get("name", ""),
            "timeout": float(headers.get("timeout", 0)),
            "total_size": int(headers.get("total_size", 0)),
            "header_size": int(headers.get("header_size", 0)),
            "dendrite": extract_info("bt_header_dendrite"),
            "axon": extract_info("bt_header_axon"),
            "encrytped_data": self.encrypted_data,
            "curve": self.curve,
            "g": self.g,
            "h": self.h,
            "seed": self.seed,
            "randomness": self.randomness,
            "commitment": self.commitment,
            "signature": self.signature,
            "commitment_hash": self.commitment_hash,
        }


class StoreUser(bt.Synapse):
    # Data to store
    encrypted_data: str  # base64 encoded string of encrypted data (bytes)
    encryption_payload: str  # encrypted json serialized bytestring of encryption params

    data_hash: typing.Optional[str] = None  # Miner storage lookup key

    required_hash_fields: typing.List[str] = pydantic.Field(
        ["encrypted_data", "encryption_payload"],
        title="Required Hash Fields",
        description="A list of required fields for the hash.",
        allow_mutation=False,
    )


class Challenge(bt.Synapse):
    # Query parameters
    challenge_hash: str  # hash of the data to challenge
    challenge_index: int  # block indices to challenge
    chunk_size: int  # bytes (e.g. 1024) for how big the chunks should be

    # Setup parameters
    g: str  # base point   (hex string representation)
    h: str  # random point (hex string representation)
    curve: str
    seed: typing.Union[str, int]  # random seed for the commitment

    # Returns
    # - commitment hash (hex string) hash( hash( data + prev_seed ) + seed )
    # - commitment (point represented as hex string)
    # - data chunk (base64 encoded string of bytes)
    # - random value (int)
    # - merkle proof (List[Dict[<left|right>, hex strings])
    # - merkle root (hex string)
    commitment_hash: typing.Optional[str] = None
    commitment_proof: typing.Optional[str] = None
    commitment: typing.Optional[str] = None
    data_chunk: typing.Optional[bytes] = None
    randomness: typing.Optional[int] = None
    merkle_proof: typing.Optional[
        typing.Union[typing.List[typing.Dict[str, str]], str]
    ] = None
    merkle_root: typing.Optional[str] = None

    required_hash_fields: typing.List[str] = pydantic.Field(
        [  # TODO: can this be done? I want to verify that these values haven't changed, but
            # they are None intially...
            "commitment_hash",
            "commitment_proof",
            "commitment",
            "data_chunk",
            "randomness",
            "merkle_proof",
            "merkle_root",
        ],
        title="Required Hash Fields",
        description="A list of required fields for the hash.",
        allow_mutation=False,
    )


class Retrieve(bt.Synapse):
    # Where to find the data
    data_hash: str  # Miner storage lookup key
    seed: str  # New random seed to hash the data with

    # Fetched data and proof
    data: typing.Optional[str] = None
    commitment_hash: typing.Optional[str] = None
    commitment_proof: typing.Optional[str] = None

    required_hash_fields: typing.List[str] = pydantic.Field(
        ["data", "data_hash", "seed", "commtiment_proof", "commitment_hash"],
        title="Required Hash Fields",
        description="A list of required fields for the hash.",
        allow_mutation=False,
    )


class RetrieveUser(bt.Synapse):
    # Where to find the data
    data_hash: str  # Miner storage lookup key

    # Fetched data to return along with AES payload in base64 encoding
    encrypted_data: typing.Optional[str] = None
    encryption_payload: typing.Optional[str] = None

    required_hash_fields: typing.List[str] = pydantic.Field(
        ["data_hash"],
        title="Required Hash Fields",
        description="A list of required fields for the hash.",
        allow_mutation=False,
    )
