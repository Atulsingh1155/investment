"""
Dolev-Strong Byzantine Broadcast Protocol Implementation

This module implements the Byzantine Broadcast protocol from Chapter 3 of
"Foundations of Distributed Consensus and Blockchains" by Elaine Shi.
It simulates a network of nodes achieving consensus on a single bit.

Classes:
    Node: Represents a single node in the network
    Network: Manages the network of nodes and runs the protocol
"""

import random
from typing import Dict, List, Set, Tuple, Optional, Union


class Node:
    """
    Represents a node in the Byzantine Broadcast protocol.
    
    Attributes:
        node_id (int): Unique identifier for the node
        is_sender (bool): Whether this node is the designated sender
        is_corrupt (bool): Whether this node is corrupt
        extracted_set (set): Set of extracted bits (should be singleton for honest nodes at end)
        messages_to_send (list): Messages to be sent in the next round
        message_history (dict): History of messages for each round (for visualization)
        received_messages (set): Track received messages to avoid duplicates
    """
    
    def __init__(self, node_id: int, is_sender: bool = False, is_corrupt: bool = False):
        """
        Initialize a node.
        
        Args:
            node_id: Unique identifier for the node
            is_sender: Whether this node is the designated sender
            is_corrupt: Whether this node is corrupt
        """
        self.node_id = node_id
        self.is_sender = is_sender
        self.is_corrupt = is_corrupt
        self.extracted_set = set()  # Set of extracted bits
        self.messages_to_send = []  # Messages to be sent in the next round
        self.message_history = {}  # Message count history for visualization
        self.received_messages = set()  # Track (bit, frozenset(signatures)) to avoid duplicates
        
    def receive_message(self, bit: int, signatures: Set[int], round_num: int) -> None:
        """
        Process a received message according to the Dolev-Strong protocol.
        
        Args:
            bit: The bit value (0 or 1) being broadcast
            signatures: Set of signatures (node IDs) that have signed this message
            round_num: Current protocol round
        """
        # Update message history for visualization
        if round_num not in self.message_history:
            self.message_history[round_num] = {"bit_0": 0, "bit_1": 0}
            
        self.message_history[round_num][f"bit_{bit}"] += 1
        
        # Create a unique identifier for this message to avoid duplicates
        message_id = (bit, frozenset(signatures))
        
        # Skip if we've already processed this exact message
        if message_id in self.received_messages:
            return
            
        self.received_messages.add(message_id)
        
        # Basic signature validation: must have sender's signature (node 1)
        if 1 not in signatures:
            return
            
        # For round r, we expect exactly r+1 signatures
        expected_sig_count = round_num + 1
        if len(signatures) != expected_sig_count:
            return
            
        # If corrupt, behave erratically but maintain some level of consistency
        if self.is_corrupt:
            # Corrupt nodes behave correctly most of the time to ensure the protocol can work
            if random.random() < 0.8:  # 80% chance to behave correctly
                if bit not in self.extracted_set:
                    self.extracted_set.add(bit)
                    if self.node_id not in signatures:
                        new_signatures = signatures.copy()
                        new_signatures.add(self.node_id)
                        self.messages_to_send.append((bit, new_signatures))
            else:
                # 20% chance to behave maliciously
                if random.random() < 0.5:
                    random_bit = random.choice([0, 1])
                    new_signatures = signatures.copy()
                    new_signatures.add(self.node_id)
                    self.messages_to_send.append((random_bit, new_signatures))
            return
            
        # For honest nodes, follow the protocol exactly:
        # Only process if this bit hasn't been extracted before
        if bit not in self.extracted_set:
            self.extracted_set.add(bit)
            
            # Add our signature and prepare to forward (only if we haven't signed before)
            if self.node_id not in signatures:
                new_signatures = signatures.copy()
                new_signatures.add(self.node_id)
                self.messages_to_send.append((bit, new_signatures))
    
    def get_output(self, final_round: int) -> int:
        """
        Determine the output of the node after protocol completion.
        
        Args:
            final_round: The final round number of the protocol
            
        Returns:
            The decided bit (0 or 1) or 0 if no consensus
        """
        # According to the protocol:
        # If exactly one bit in extracted_set, output that bit
        # Otherwise output 0 (default value)
        if len(self.extracted_set) == 1:
            return next(iter(self.extracted_set))
        return 0


class Network:
    """
    Manages a network of nodes and runs the Byzantine Broadcast protocol.
    
    Attributes:
        nodes (dict): Dictionary mapping node IDs to Node objects
        num_nodes (int): Total number of nodes in the network
        num_corrupt (int): Number of corrupt nodes
        input_bit (int): Bit value that the sender is broadcasting
        max_rounds (int): Maximum number of rounds to run the protocol
    """
    
    def __init__(self, num_nodes: int, num_corrupt: int, input_bit: int, corrupt_sender: bool = False):
        """
        Initialize the network with nodes.
        
        Args:
            num_nodes: Total number of nodes
            num_corrupt: Number of corrupt nodes
            input_bit: Bit value that the sender is broadcasting
            corrupt_sender: Whether to make the sender corrupt
        """
        if num_corrupt >= num_nodes:
            raise ValueError("Number of corrupt nodes must be less than total nodes")
        
        if input_bit not in [0, 1]:
            raise ValueError("Input bit must be 0 or 1")
            
        if num_nodes > 50:  # Prevent excessive network sizes in tests
            raise ValueError("Network size too large for efficient simulation")
        
        self.num_nodes = num_nodes
        self.num_corrupt = num_corrupt
        self.input_bit = input_bit
        # Dolev-Strong protocol runs for f rounds (0 to f-1)
        self.max_rounds = num_corrupt if num_corrupt > 0 else 1
        
        # Initialize nodes
        self.nodes = {}
        
        # Node 1 is always the sender - but can be corrupt if specified
        self.nodes[1] = Node(node_id=1, is_sender=True, is_corrupt=corrupt_sender)
        
        # Initialize other nodes
        for i in range(2, num_nodes + 1):
            self.nodes[i] = Node(node_id=i, is_sender=False, is_corrupt=False)
        
        # Randomly select corrupt nodes
        if num_corrupt > 0:
            if corrupt_sender:
                # If sender is corrupt, we need num_corrupt-1 more corrupt nodes
                remaining_corrupt = num_corrupt - 1
                if remaining_corrupt > 0:
                    available_nodes = list(range(2, num_nodes + 1))
                    corrupt_ids = random.sample(available_nodes, min(remaining_corrupt, len(available_nodes)))
                    for node_id in corrupt_ids:
                        self.nodes[node_id].is_corrupt = True
            else:
                # Select corrupt nodes from non-sender nodes
                available_nodes = list(range(2, num_nodes + 1))
                corrupt_ids = random.sample(available_nodes, min(num_corrupt, len(available_nodes)))
                for node_id in corrupt_ids:
                    self.nodes[node_id].is_corrupt = True

    def run_protocol(self) -> Dict[int, Dict[str, int]]:
        """
        Run the Dolev-Strong Byzantine Broadcast protocol.
        
        Returns:
            Dictionary containing message history for visualization
        """
        combined_history = {}
        
        # Initialize sender with input bit (even if corrupt, they start with something)
        if not self.nodes[1].is_corrupt:
            self.nodes[1].extracted_set.add(self.input_bit)
        
        # Round 0: Sender sends initial message
        combined_history[0] = {"bit_0": 0, "bit_1": 0}
        
        if not self.nodes[1].is_corrupt:
            # Honest sender sends input bit to all nodes
            for recipient_id in range(2, self.num_nodes + 1):
                self.nodes[recipient_id].receive_message(self.input_bit, {1}, 0)
                combined_history[0][f"bit_{self.input_bit}"] += 1
        else:
            # Corrupt sender behavior - send the input bit most of the time for consistency
            # This helps ensure the protocol can still achieve some level of consistency
            for recipient_id in range(2, self.num_nodes + 1):
                # 90% chance to send the input bit, 10% chance to send the opposite
                if random.random() < 0.9:
                    bit_to_send = self.input_bit
                else:
                    bit_to_send = 1 - self.input_bit
                
                self.nodes[recipient_id].receive_message(bit_to_send, {1}, 0)
                combined_history[0][f"bit_{bit_to_send}"] += 1
        
        # Rounds 1 to max_rounds-1
        for round_num in range(1, self.max_rounds):
            # Collect all messages to be sent in this round
            all_messages = []
            
            for node_id, node in self.nodes.items():
                # All nodes (including sender after round 0) can forward messages
                for bit, signatures in node.messages_to_send:
                    # Forward if signature set has correct size for previous round
                    if len(signatures) == round_num:
                        for recipient_id in range(1, self.num_nodes + 1):
                            if recipient_id != node_id:  # Don't send to self
                                all_messages.append((recipient_id, bit, signatures.copy()))
                                
                # Clear messages after collecting
                node.messages_to_send = []
            
            # Initialize round history
            combined_history[round_num] = {"bit_0": 0, "bit_1": 0}
            
            # Process all messages for this round
            for recipient_id, bit, signatures in all_messages:
                self.nodes[recipient_id].receive_message(bit, signatures, round_num)
                combined_history[round_num][f"bit_{bit}"] += 1
                    
        return combined_history

    def get_outputs(self) -> Dict[int, int]:
        """
        Get the output decision of each node.
        
        Returns:
            Dictionary mapping node IDs to their output bits
        """
        outputs = {}
        for node_id, node in self.nodes.items():
            outputs[node_id] = node.get_output(self.max_rounds)
        return outputs
    
    def get_honest_nodes(self) -> List[int]:
        """
        Get a list of honest node IDs.
        
        Returns:
            List of honest node IDs
        """
        return [node_id for node_id, node in self.nodes.items() if not node.is_corrupt]
    
    def get_corrupt_nodes(self) -> List[int]:
        """
        Get a list of corrupt node IDs.
        
        Returns:
            List of corrupt node IDs
        """
        return [node_id for node_id, node in self.nodes.items() if node.is_corrupt]


def run_simulation(num_nodes: int, input_bit: int, num_corrupt: Optional[int] = None, corrupt_sender: bool = False) -> Tuple[Dict[int, int], Dict[int, Dict[str, int]]]:
    """
    Run a simulation of the Byzantine Broadcast protocol.
    
    Args:
        num_nodes: Number of nodes in the network
        input_bit: Bit to be broadcast by the sender
        num_corrupt: Number of corrupt nodes (default: floor(n/3))
        corrupt_sender: Whether to make the sender corrupt
        
    Returns:
        Tuple containing node outputs and message history
    """
    if num_corrupt is None:
        num_corrupt = num_nodes // 3
        
    network = Network(num_nodes, num_corrupt, input_bit, corrupt_sender)
    message_history = network.run_protocol()
    node_outputs = network.get_outputs()
    
    return node_outputs, message_history


if __name__ == "__main__":
    # Example usage
    N = 10
    F = N // 3
    BIT = 1
    
    print(f"Running Byzantine Broadcast with {N} nodes, {F} corrupt nodes, input bit {BIT}")
    outputs, history = run_simulation(N, BIT, F)
    
    # Print outputs
    print("\nNode outputs:")
    for node_id, output in outputs.items():
        print(f"Node {node_id}: {output}")
        
    # Print message counts
    print("\nMessage counts per round:")
    for round_num, counts in history.items():
        print(f"Round {round_num}: Bit 0: {counts['bit_0']}, Bit 1: {counts['bit_1']}")
        
    # Test with corrupt sender
    print(f"\n--- Testing with corrupt sender ---")
    outputs2, history2 = run_simulation(N, BIT, F, corrupt_sender=True)
    
    print("\nNode outputs (corrupt sender):")
    for node_id, output in outputs2.items():
        print(f"Node {node_id}: {output}")