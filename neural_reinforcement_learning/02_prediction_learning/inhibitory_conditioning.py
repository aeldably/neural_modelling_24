from abc_classical_conditioning_paradigm import ClassicalConditioningParadigm


class InhibitoryConditioning(ClassicalConditioningParadigm):

    def pre_training(self, pre_training_trials=0):
        """Define the pre-training phase, if applicable."""
        pass

    def training(self, training_trials=0):
        """
        Parameters:
        - training_trials (int): Number of training trials
        """
        for trial in range(training_trials):
            if trial % 2 == 0:
                # present S1 alone with a reward to build a positive association
                present_stimuli = ["S1"]
                reward = self.max_reward  # Reward is given
            else:
                # present S1 and S2 together with no reward to build inhibition
                present_stimuli = ["S1", "S2"]
                reward = 0.0

            self.update_associative_strength(present_stimuli, reward)


train_trials = 100

inhibitory_conditioning = InhibitoryConditioning(learning_rate_1=0.1,
                                                 learning_rate_2=0.1,
                                                 max_reward=1.0)
inhibitory_conditioning.run(training_trials=train_trials)
inhibitory_conditioning.plot_history("Inhibitory Conditioning Paradigm")