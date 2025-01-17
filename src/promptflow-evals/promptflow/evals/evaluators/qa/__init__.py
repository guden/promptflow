# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

__path__ = __import__("pkgutil").extend_path(__path__, __name__)  # type: ignore

from concurrent.futures import ThreadPoolExecutor, as_completed

from promptflow.evals.evaluators import (
    CoherenceEvaluator,
    F1ScoreEvaluator,
    FluencyEvaluator,
    GroundednessEvaluator,
    RelevanceEvaluator,
    SimilarityEvaluator,
)


class QAEvaluator:
    def __init__(self, model_config, parallel: bool = True):
        """
        Initialize an evaluator configured for a specific Azure OpenAI model.

        :param model_config: Configuration for the Azure OpenAI model.
        :type model_config: AzureOpenAIModelConfiguration
        :return: A function that evaluates and generates metrics for "question-answering" scenario.
        :rtype: function

        **Usage**

        .. code-block:: python

            eval_fn = QAEvaluator(model_config)
            result = qa_eval(
                question="Tokyo is the capital of which country?",
                answer="Japan",
                context="Tokyo is the capital of Japan.",
                ground_truth="Japan"
            )
        """
        self._parallel = parallel

        self._evaluators = [
            GroundednessEvaluator(model_config),
            RelevanceEvaluator(model_config),
            CoherenceEvaluator(model_config),
            FluencyEvaluator(model_config),
            SimilarityEvaluator(model_config),
            F1ScoreEvaluator(),
        ]

    def __call__(self, *, question: str, answer: str, context: str, ground_truth: str, **kwargs):
        """Evaluates question-answering scenario.

        :param question: The question to be evaluated.
        :type question: str
        :param answer: The answer to be evaluated.
        :type answer: str
        :param context: The context to be evaluated.
        :type context: str
        :param ground_truth: The ground truth to be evaluated.
        :type ground_truth: str
        :param parallel: Whether to evaluate in parallel. Defaults to True.
        :type parallel: bool
        :return: The scores for QA scenario.
        :rtype: dict
        """
        results = {}
        if self._parallel:
            with ThreadPoolExecutor() as executor:
                # Create a future for each evaluator
                futures = {
                    executor.submit(
                        evaluator,
                        question=question,
                        answer=answer,
                        context=context,
                        ground_truth=ground_truth,
                        **kwargs
                    ): evaluator
                    for evaluator in self._evaluators
                }

                # Collect results as they complete
                for future in as_completed(futures):
                    results.update(future.result())
        else:
            for evaluator in self._evaluators:
                results.update(
                    evaluator(question=question, answer=answer, context=context, ground_truth=ground_truth, **kwargs)
                )

        return results
