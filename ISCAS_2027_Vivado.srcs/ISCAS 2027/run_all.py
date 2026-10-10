from generate_stimuli import main as stimuli_main
from photoreceptor_reference import main as reference_main
from run_reference_experiments import main as experiment_main
from compare_models import run_comparisons, run_step_size_convergence
from run_adaptive_experiments import run_experiments as run_adaptive_experiments
from generate_results import generate_provisional_reference_figures


if __name__ == "__main__":
    stimuli_main()
    reference_main()
    experiment_main()
    run_comparisons()
    run_step_size_convergence()
    run_adaptive_experiments()
    generate_provisional_reference_figures()
    print("Provisional Python experiment pipeline completed; outputs are not paper-validated.")
