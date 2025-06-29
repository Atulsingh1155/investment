"""
Visualization for Byzantine Broadcast Protocol

This module provides visualization functionality for the Dolev-Strong Byzantine
Broadcast protocol, showing message counts for bits 0 and 1 over protocol rounds.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Optional
import sys
import os

# Add the current directory to the path so we can import byzantine_broadcast
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from byzantine_broadcast import run_simulation
except ImportError:
    print("Error: Could not import byzantine_broadcast module")
    print("Make sure byzantine_broadcast.py is in the same directory as this file")
    sys.exit(1)


def visualize_message_history(
    history: Dict[int, Dict[str, int]],
    title: str = "Byzantine Broadcast: Message Count per Round",
    save_path: Optional[str] = None
) -> None:
    """
    Create a visualization of the message counts during the protocol execution.
    
    Args:
        history: Dictionary containing message counts per round
        title: Title for the plot
        save_path: Optional path to save the plot instead of showing it
    """
    if not history:
        print("Warning: No message history data to visualize")
        return
    
    # Extract rounds and message counts
    rounds = sorted(history.keys())
    bit_0_counts = [history[r].get("bit_0", 0) for r in rounds]
    bit_1_counts = [history[r].get("bit_1", 0) for r in rounds]
    
    # Prepare plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create bar positions
    x = np.arange(len(rounds))
    width = 0.35
    
    # Plot bars with better styling
    bars1 = ax.bar(x - width/2, bit_0_counts, width, label='Bit 0', 
                   alpha=0.8, color='lightcoral', edgecolor='darkred', linewidth=1)
    bars2 = ax.bar(x + width/2, bit_1_counts, width, label='Bit 1', 
                   alpha=0.8, color='lightblue', edgecolor='darkblue', linewidth=1)
    
    # Add labels and formatting
    ax.set_xlabel('Protocol Round', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Messages', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Round {r}" for r in rounds], rotation=45 if len(rounds) > 5 else 0)
    ax.legend(fontsize=11)
    
    # Add grid for better readability
    ax.grid(True, linestyle='--', alpha=0.3, axis='y')
    ax.set_axisbelow(True)
    
    # Add value annotations on top of each bar
    def add_value_labels(bars, counts):
        for bar, count in zip(bars, counts):
            if count > 0:
                height = bar.get_height()
                ax.annotate(f'{count}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),  # 3 points vertical offset
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=10, fontweight='bold')
    
    add_value_labels(bars1, bit_0_counts)
    add_value_labels(bars2, bit_1_counts)
    
    # Add summary statistics
    total_bit_0 = sum(bit_0_counts)
    total_bit_1 = sum(bit_1_counts)
    total_messages = total_bit_0 + total_bit_1
    
    stats_text = f"Total Messages: {total_messages}\nBit 0: {total_bit_0} ({total_bit_0/total_messages*100:.1f}%)\nBit 1: {total_bit_1} ({total_bit_1/total_messages*100:.1f}%)" if total_messages > 0 else "No messages"
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {save_path}")
    else:
        plt.show()
    
    plt.close()


def visualize_protocol_run(
    num_nodes: int, 
    input_bit: int, 
    num_corrupt: Optional[int] = None,
    save_path: Optional[str] = None
) -> Tuple[Dict[int, int], Dict[int, Dict[str, int]]]:
    """
    Run the protocol and visualize the results.
    
    Args:
        num_nodes: Number of nodes in the network
        input_bit: Bit value to be broadcast
        num_corrupt: Number of corrupt nodes (default: n/3)
        save_path: Optional path to save the plot
        
    Returns:
        Tuple containing node outputs and message history
    """
    # Set default for corrupt nodes
    if num_corrupt is None:
        num_corrupt = num_nodes // 3
        
    print(f"Running Byzantine Broadcast simulation:")
    print(f"  - Nodes: {num_nodes}")
    print(f"  - Corrupt nodes: {num_corrupt}")
    print(f"  - Input bit: {input_bit}")
    print(f"  - Expected rounds: {max(num_corrupt, 1)}")
    
    try:
        # Run the simulation
        outputs, history = run_simulation(num_nodes, input_bit, num_corrupt)
        
        # Print results summary
        print(f"\nSimulation completed!")
        print(f"  - Actual rounds: {len(history)}")
        print(f"  - Total nodes: {len(outputs)}")
        
        # Analyze outputs
        bit_0_count = sum(1 for output in outputs.values() if output == 0)
        bit_1_count = sum(1 for output in outputs.values() if output == 1)
        
        print(f"  - Nodes outputting 0: {bit_0_count}")
        print(f"  - Nodes outputting 1: {bit_1_count}")
        
        # Check for consensus
        if bit_0_count == len(outputs) or bit_1_count == len(outputs):
            consensus_bit = 0 if bit_0_count == len(outputs) else 1
            print(f"  ✅ Consensus achieved on bit {consensus_bit}")
        else:
            print(f"  ⚠️  No consensus achieved")
        
        # Prepare visualization title
        title = f"Byzantine Broadcast: {num_nodes} Nodes, {num_corrupt} Corrupt, Input Bit {input_bit}"
        
        # Display results
        visualize_message_history(history, title, save_path)
        
        return outputs, history
        
    except Exception as e:
        print(f"Error during simulation: {e}")
        return {}, {}


def compare_scenarios() -> None:
    """Compare multiple Byzantine Broadcast scenarios side by side."""
    scenarios = [
        {"nodes": 10, "corrupt": 3, "input_bit": 1, "title": "Standard (n=10, f=3)"},
        {"nodes": 10, "corrupt": 0, "input_bit": 1, "title": "No Corruption (n=10, f=0)"},
        {"nodes": 15, "corrupt": 5, "input_bit": 0, "title": "Larger Network (n=15, f=5)"},
        {"nodes": 7, "corrupt": 2, "input_bit": 1, "title": "Small Network (n=7, f=2)"}
    ]
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    
    for i, scenario in enumerate(scenarios):
        try:
            outputs, history = run_simulation(
                scenario["nodes"], 
                scenario["input_bit"], 
                scenario["corrupt"]
            )
            
            # Extract data for this subplot
            rounds = sorted(history.keys())
            bit_0_counts = [history[r].get("bit_0", 0) for r in rounds]
            bit_1_counts = [history[r].get("bit_1", 0) for r in rounds]
            
            # Plot on subplot
            x = np.arange(len(rounds))
            width = 0.35
            
            axes[i].bar(x - width/2, bit_0_counts, width, label='Bit 0', alpha=0.8, color='lightcoral')
            axes[i].bar(x + width/2, bit_1_counts, width, label='Bit 1', alpha=0.8, color='lightblue')
            
            axes[i].set_title(scenario["title"], fontweight='bold')
            axes[i].set_xlabel('Round')
            axes[i].set_ylabel('Messages')
            axes[i].set_xticks(x)
            axes[i].set_xticklabels([f"R{r}" for r in rounds])
            axes[i].legend()
            axes[i].grid(True, alpha=0.3)
            
            # Add consensus info
            bit_0_nodes = sum(1 for output in outputs.values() if output == 0)
            bit_1_nodes = sum(1 for output in outputs.values() if output == 1)
            consensus_text = f"Consensus: {'✅' if (bit_0_nodes == len(outputs) or bit_1_nodes == len(outputs)) else '❌'}"
            axes[i].text(0.02, 0.98, consensus_text, transform=axes[i].transAxes, 
                        verticalalignment='top', fontsize=10,
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
        except Exception as e:
            axes[i].text(0.5, 0.5, f"Error: {str(e)}", transform=axes[i].transAxes,
                        ha='center', va='center', fontsize=12, color='red')
            axes[i].set_title(f"{scenario['title']} - Failed", fontweight='bold', color='red')
    
    plt.tight_layout()
    plt.suptitle("Byzantine Broadcast Protocol Comparison", fontsize=16, fontweight='bold', y=0.98)
    plt.subplots_adjust(top=0.93)
    plt.show()


def visualize_multiple_scenarios() -> None:
    """Visualize multiple protocol scenarios for comparison."""
    print("=== Byzantine Broadcast Protocol Visualization ===")
    print("Running multiple scenarios to demonstrate protocol behavior...\n")
    
    scenarios = [
        {"name": "Standard case", "nodes": 10, "corrupt": 3, "input_bit": 1},
        {"name": "No corruption", "nodes": 10, "corrupt": 0, "input_bit": 0},
        {"name": "High corruption", "nodes": 15, "corrupt": 4, "input_bit": 1},
        {"name": "Small network", "nodes": 7, "corrupt": 2, "input_bit": 0}
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- Scenario {i}: {scenario['name']} ---")
        outputs, history = visualize_protocol_run(
            scenario["nodes"], 
            scenario["input_bit"], 
            scenario["corrupt"]
        )
        
        if i < len(scenarios):
            input("\nPress Enter to continue to the next scenario...")
    
    print(f"\n=== All individual scenarios completed! ===")
    print("Now showing comparison view...")
    compare_scenarios()


def interactive_visualization() -> None:
    """Interactive mode for custom protocol visualization."""
    print("\n=== Interactive Byzantine Broadcast Visualization ===")
    
    while True:
        try:
            print("\nEnter parameters for Byzantine Broadcast simulation:")
            num_nodes = int(input("Number of nodes (4-20): "))
            if num_nodes < 4 or num_nodes > 20:
                print("Please enter a number between 4 and 20")
                continue
                
            max_corrupt = num_nodes - 1
            num_corrupt = int(input(f"Number of corrupt nodes (0-{max_corrupt}): "))
            if num_corrupt < 0 or num_corrupt >= num_nodes:
                print(f"Please enter a number between 0 and {max_corrupt}")
                continue
                
            input_bit = int(input("Input bit (0 or 1): "))
            if input_bit not in [0, 1]:
                print("Please enter 0 or 1")
                continue
                
            # Run visualization
            visualize_protocol_run(num_nodes, input_bit, num_corrupt)
            
            # Ask if user wants to continue
            again = input("\nRun another simulation? (y/n): ").lower().strip()
            if again not in ['y', 'yes']:
                break
                
        except ValueError:
            print("Please enter valid numbers")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    print("Byzantine Broadcast Protocol Visualization")
    print("==========================================")
    
    # Check if matplotlib is available
    try:
        plt.figure()
        plt.close()
    except Exception as e:
        print(f"Error: matplotlib not properly configured: {e}")
        print("Please install matplotlib: pip install matplotlib")
        sys.exit(1)
    
    print("Choose visualization mode:")
    print("1. Pre-defined scenarios")
    print("2. Interactive custom scenarios")
    print("3. Single test run")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            print("\nRunning pre-defined scenarios...")
            print("Close each plot window to continue to the next scenario.")
            visualize_multiple_scenarios()
            
        elif choice == "2":
            interactive_visualization()
            
        elif choice == "3":
            print("\nRunning single test with default parameters...")
            visualize_protocol_run(10, 1, 3)
            
        else:
            print("Invalid choice. Running default scenario...")
            visualize_protocol_run(10, 1, 3)
            
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nVisualization completed!")
    print("\nTo run custom scenarios programmatically:")
    print("  python -c \"from visualize_broadcast import visualize_protocol_run; "
          "visualize_protocol_run(num_nodes=15, input_bit=1, num_corrupt=4)\"")