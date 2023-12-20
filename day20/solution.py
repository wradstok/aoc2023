from __future__ import annotations
from collections import deque
from enum import Enum
from abc import ABC, abstractmethod


class Pulse(Enum):
    LOW = 0
    HIGH = 1


class Module(ABC):
    label: str
    outputs: list[Module]

    @abstractmethod
    def receive(self, value: Pulse, queue: deque, from_module: str):
        pass

    @abstractmethod
    def send(self, queue: deque, pulses: dict[Pulse, int]):
        pass


class Broadcast(Module):
    prev_value: Pulse

    def __init__(self, label: str):
        self.label = label
        self.outputs = []

    def receive(self, value: Pulse, queue: deque, from_module: str):
        print(f"{from_module} -{value}-> {self.label} ")
        self.prev_value = value
        queue.append(self)

    def send(self, queue: deque, pulses: dict[Pulse, int]):
        pulses[self.prev_value] += len(self.outputs)
        for module in self.outputs:
            module.receive(self.prev_value, queue, self.label)


class FlipFlop(Module):
    state: str

    def __init__(self, label: str):
        self.label = label
        self.outputs = []
        self.state = "OFF"

    def receive(self, value: Pulse, queue: deque, from_module: str):
        print(f"{from_module} -{value}-> {self.label} ")
        if value == Pulse.LOW:
            queue.append(self)
            if self.state == "OFF":
                self.state = "ON"
            else:
                self.state = "OFF"

    def send(self, queue: deque, pulses: dict[Pulse, int]):
        pulse = Pulse.HIGH if self.state == "ON" else Pulse.LOW
        pulses[pulse] += len(self.outputs)

        for module in self.outputs:
            module.receive(pulse, queue, self.label)


class Conjunction(Module):
    prev_values: dict[Module, Pulse]

    def __init__(self, label: str):
        self.label = label
        self.outputs = []
        self.prev_values = {}

    def receive(self, value: Pulse, queue: deque, from_module: Module):
        print(f"{from_module} -{value}-> {self.label} ")
        self.prev_values[from_module] = value
        queue.append(self)

    def send(self, queue: deque, pulses: dict[Pulse, int]):
        pulse = Pulse.HIGH
        if all(value == Pulse.HIGH for value in self.prev_values.values()):
            pulse = pulse.LOW

        for module in self.outputs:
            module.receive(pulse, queue, self.label)
        pulses[pulse] += len(self.outputs)


modules = dict()

with open("day20/input.txt") as f:
    lines = f.read().splitlines()

    # Create all modules that output something
    for line in lines:
        src = line.split(" -> ")[0]
        match line[0]:
            case "b":
                modules[src] = Broadcast(src)
            case "%":
                modules[src[1:]] = FlipFlop(src[1:])
            case "&":
                modules[src[1:]] = Conjunction(src[1:])

    for line in lines:
        src = line.split(" -> ")[0]
        targets = line.split(" -> ")[1].split(", ")

        # Any unattached outputs
        for target in targets:
            if target not in modules:
                modules[target] = FlipFlop(target)

        match line[0]:
            case "b":
                for target in targets:
                    modules[src].outputs.append(modules[target])
            case _:
                for target in targets:
                    modules[src[1:]].outputs.append(modules[target])

# Initialize all conjunctions to LOW
for module in modules.values():
    for output in module.outputs:
        if type(output) == Conjunction:
            output.prev_values[module.label] = Pulse.LOW


# Part 1
pulses: dict[Pulse, int] = {Pulse.LOW: 0, Pulse.HIGH: 0}
presses = 1000
for i in range(presses):
    actions: deque[Module] = deque()
    modules["broadcaster"].receive(Pulse.LOW, actions, "button")
    pulses[Pulse.LOW] += 1

    while actions:
        module = actions.popleft()
        module.send(actions, pulses)

print(pulses[Pulse.HIGH] * pulses[Pulse.LOW])
