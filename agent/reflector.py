# Reflection module: Evaluate improvements and provide feedback for PPO
from tools.metrics import calculate_reward

class Reflector:
    def reflect(self, original_code, improved_code, language):
        """
        Computes a multi-dimensional reward and generates detailed reflection notes
        by delegating to the metrics module.
        
        Args:
            original_code (str): The initial code snippet.
            improved_code (str): The code snippet after suggestions were applied.
            language (str): The programming language ('python' or 'javascript').

        Returns:
            tuple: A tuple containing the float reward score and a string with
                   detailed notes on the metric changes.
        """
        reward, notes = calculate_reward(
            original_code,
            improved_code,
            language
        )
        return reward, notes
