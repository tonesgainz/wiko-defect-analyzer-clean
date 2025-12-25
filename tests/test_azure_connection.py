import os
import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_AZURE_INTEGRATION") != "1",
        reason="Set RUN_AZURE_INTEGRATION=1 to run live Azure Foundry integration test",
    ),
]


def test_azure_project_client_connects():
    # Imports inside test so collection never fails on SDK churn.
    from azure.identity import DefaultAzureCredential
    from azure.ai.projects import AIProjectClient

    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)
    assert client is not None
