import os
import logging
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import *
import numpy as np

PACKNUM_CEIL = 20
PACKNUM_FLOOR = 1

ADDRESS = 0x49

def hex_to_binarray(n):
    arr = [1 if digit=='1' else 0 for digit in bin(n)[2:]]
    # while len(arr) < 8:
    #     arr.insert(0, 0)
    return arr

async def wt(n, dut):
    for _ in range(n):
        await FallingEdge(dut.clock)

async def send_bit(bit, dut):
    await wt(3, dut)
    dut.SDA_in.value = bit
    await wt(2, dut)
    dut.SCL.value = 1
    await wt(5, dut)
    dut.SCL.value = 0

async def send_data(address, array, dut):
    # Address: int, array: data array of bits
    dut.SDA_in.value = 1
    dut.SCL.value = 1
    await FallingEdge(dut.clock)
    dut.SDA_in.value = 0
    await FallingEdge(dut.clock)
    dut.SCL.value = 0
    await wt(2, dut)
    for i in hex_to_binarray(address):
        await send_bit(i, dut)
    await send_bit(0, dut)
    await wt(3, dut)
    dut.SDA_in.value = 1
    await wt(1, dut)
    assert(dut.ack.value == 1)
    await wt(1, dut)
    dut.SCL.value = 1
    await wt(5, dut)
    # dut.SCL.value = 0
    #! RELEASE_WIRE, wait, and assert SDA_out is low and wr_up is high
    await wt(2, dut)
    dut.SCL.value = 1
    await wt(5, dut)
    dut.SCL.value = 0
    for subarray in array:
        print("Subarray to send:")
        print(subarray)
        for element in subarray:
            await send_bit(element, dut)
        await wt(3, dut)
        dut.SDA_in.value = 1

        await wt(1, dut)
        assert(dut.ack.value == 1)
        await wt(1, dut)
        dut.SCL.value = 1
        await wt(5, dut)
        # dut.SCL.value = 0
        #! RELEASE_WIRE, wait, and assert SDA_out is low and wr_up is high
        await wt(2, dut)
        dut.SCL.value = 1
        await wt(5, dut)
        dut.SCL.value = 0
        await wt(5, dut)
        payload = int("".join(str(x) for x in subarray), 2)
        assert(dut.data_out.value == payload)
    dut.SCL.value = 0
    dut.SDA_in.value = 0
    await wt(1, dut)
    dut.SCL.value = 1
    await wt(1, dut)
    dut.SDA_in.value = 1

async def read_bit(dut):
    await wt(3, dut)
    await wt(2, dut)
    dut.SCL.value = 1
    await wt(2, dut)
    value = dut.SDA_out.value
    await wt(3, dut)
    dut.SCL.value = 0
    return value

async def recv_data(address, array, dut):
    # Address: int, array: array of bytes
    dut.SDA_in.value = 1
    dut.SCL.value = 1
    await FallingEdge(dut.clock)
    dut.SDA_in.value = 0
    await FallingEdge(dut.clock)
    dut.SCL.value = 0
    await wt(2, dut)
    for i in hex_to_binarray(address):
        await send_bit(i, dut)
    await send_bit(1, dut)
    #! RELEASE_WIRE, wait, and assert SDA_out is low and wr_up is high
    await wt(3, dut)
    dut.SDA_in.value = 1
    await wt(1, dut)
    assert(dut.ack.value == 1)
    await wt(1, dut)
    dut.SCL.value = 1
    await wt(5, dut)
    dut.SCL.value = 0
    # todo: put thing in array.
    for i in range(len(array)):
        received_bit = []
        await wt(2, dut)
        dut.SCL.value = 1
        dut.data_in.value = array[i]
        dut.data_incoming.value = 1
        await wt(5, dut)
        dut.data_incoming.value = 0
        dut.SCL.value = 0
        for j in range(8):
            bit = await read_bit(dut)
            received_bit.append(bit)
        #! DUT Releases wire, wait, and assert SDA_out is low and wr_up is high
        if (i == len(array)-1):
            dut.SDA_in.value = 1
        else:
            dut.SDA_in.value = 0
        await wt(2, dut)
        dut.SCL.value = 1
        await wt(5, dut)
        dut.SCL.value = 0
        await wt(2, dut)
        dut.SDA_in.value = 1
        payload = int("".join(str(x) for x in received_bit), 2)
        print(received_bit)
        assert(array[i] == payload)
    dut.SCL.value = 0
    dut.SDA_in.value = 0
    await wt(1, dut)
    dut.SCL.value = 1
    await wt(1, dut)
    dut.SDA_in.value = 1

def generate_down_packet():
    rand_packet_count = random.randint(PACKNUM_FLOOR, PACKNUM_CEIL+1)
    arr = []
    for i in range (rand_packet_count):
        packet = []
        for i in range(8):
            bit = int(np.random.choice([0,1]))
            packet.append(bit)
        arr.append(packet)
    return arr

def generate_up_packet():
    rand_packet_count = random.randint(PACKNUM_FLOOR, PACKNUM_CEIL+1)
    arr = []
    for i in range (rand_packet_count):
        packet = random.randint(0, 2**8-1)
        arr.append(packet)
    return arr
    

@cocotb.test()
async def basic_test(dut):
    print("============== STARTING TEST ==============")
    # Determinism
    random.seed(42)
    # Run the clock
    cocotb.start_soon(Clock(dut.clock, 10, units="ns").start())

    # Since our circuit is on the rising edge,
    # we can feed inputs on the falling edge
    # This makes things easier to read and visualize
    await FallingEdge(dut.clock)

    # Reset the DUT
    dut.reset.value = False
    await FallingEdge(dut.clock)
    await FallingEdge(dut.clock)
    dut.reset.value = True

    for i in range(20):
        package_down = generate_down_packet()
        await send_data(ADDRESS, package_down, dut)
        package_up = generate_up_packet()
        await recv_data(ADDRESS, package_up, dut)
