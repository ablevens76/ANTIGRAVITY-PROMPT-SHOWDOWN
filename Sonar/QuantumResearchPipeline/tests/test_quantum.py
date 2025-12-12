"""
Tests for quantum_simulator.py
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from quantum_simulator import (
    create_toric_code_circuit,
    create_anyon_braiding_circuit,
    create_surface_code_circuit,
    run_simulation,
    calculate_error_rate,
)


class TestCircuitCreation:
    """Test quantum circuit generation."""
    
    def test_toric_code_circuit_creation(self):
        """Test toric code circuit is created correctly."""
        qc = create_toric_code_circuit(size=2)
        assert qc is not None
        assert qc.num_qubits >= 4  # 2x2 data + ancillas
        assert qc.num_clbits == 2
    
    def test_anyon_braiding_2_qubits(self):
        """Test anyon braiding with minimum qubits."""
        qc = create_anyon_braiding_circuit(n_anyons=2)
        assert qc.num_qubits == 2
        assert qc.num_clbits >= 2  # measure_all adds classical bits
    
    def test_anyon_braiding_4_qubits(self):
        """Test anyon braiding with 4 qubits."""
        qc = create_anyon_braiding_circuit(n_anyons=4)
        assert qc.num_qubits == 4
        # Should have H gates, CZ gates, and measurements
        op_names = [instr.operation.name for instr in qc.data]
        assert 'h' in op_names
        assert 'cz' in op_names or 'swap' in op_names
    
    def test_anyon_braiding_scales(self):
        """Test anyon braiding works for various qubit counts."""
        for n in [2, 3, 4, 5, 6]:
            qc = create_anyon_braiding_circuit(n_anyons=n)
            assert qc.num_qubits == n
    
    def test_surface_code_creation(self):
        """Test surface code circuit creation."""
        qc = create_surface_code_circuit(distance=3)
        assert qc.num_qubits >= 9  # 3x3 data qubits at minimum
        assert qc.num_clbits == 3


class TestSimulation:
    """Test quantum simulation execution."""
    
    def test_run_simulation_returns_counts(self):
        """Test that simulation returns measurement counts."""
        qc = create_anyon_braiding_circuit(2)
        counts = run_simulation(qc, shots=100)
        
        assert isinstance(counts, dict)
        assert sum(counts.values()) == 100
    
    def test_simulation_with_noise(self):
        """Test noisy simulation doesn't crash."""
        qc = create_anyon_braiding_circuit(2)
        counts = run_simulation(qc, shots=100, noise_level=0.01)
        
        assert isinstance(counts, dict)
        assert sum(counts.values()) == 100


class TestErrorRateCalculation:
    """Test error rate calculation."""
    
    def test_all_correct_zero_error(self):
        """Test zero error rate when all measurements match expected."""
        counts = {"0": 100, "00": 50}
        error_rate = calculate_error_rate(counts, expected_pattern="0")
        assert error_rate == 0.0
    
    def test_all_wrong_full_error(self):
        """Test full error when no measurements match."""
        counts = {"111": 100}
        error_rate = calculate_error_rate(counts, expected_pattern="0")
        assert error_rate == 1.0
    
    def test_partial_error(self):
        """Test partial error calculation."""
        counts = {"0": 50, "1": 50}
        error_rate = calculate_error_rate(counts, expected_pattern="0")
        assert error_rate == 0.5


class TestIntegration:
    """Integration tests for full pipeline."""
    
    def test_full_simulation_pipeline(self):
        """Test complete simulation from circuit to results."""
        # Create circuit
        qc = create_toric_code_circuit(size=2)
        
        # Run simulation
        counts = run_simulation(qc, shots=1000)
        
        # Calculate error rate
        error_rate = calculate_error_rate(counts, expected_pattern="0")
        
        assert 0.0 <= error_rate <= 1.0
        assert sum(counts.values()) == 1000
