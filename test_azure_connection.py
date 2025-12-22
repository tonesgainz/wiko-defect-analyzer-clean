#!/usr/bin/env python3
"""
Test Azure AI Foundry connection and agent creation
"""

import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

# Load environment variables
load_dotenv()

user_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")

print(f"🔗 Connecting to Azure AI Project...")
print(f"   Endpoint: {user_endpoint}")

try:
    # Create project client
    project_client = AIProjectClient(
        endpoint=user_endpoint,
        credential=DefaultAzureCredential(),
    )

    print("✅ Successfully connected to Azure AI Project!")

    # Test agent creation
    agent_name = "wiko-test-agent"
    model_deployment_name = os.getenv("AZURE_VISION_DEPLOYMENT", "gpt-4-1-vision")

    print(f"\n🤖 Creating test agent...")
    print(f"   Name: {agent_name}")
    print(f"   Model: {model_deployment_name}")

    # Creates an agent, bumps the agent version if parameters have changed
    agent = project_client.agents.create_version(
        agent_name=agent_name,
        definition=PromptAgentDefinition(
            model=model_deployment_name,
            instructions="You are a storytelling agent. You craft engaging one-line stories based on user prompts and context.",
        ),
    )

    print(f"✅ Agent created successfully!")
    print(f"   Agent Name: {agent.name}")
    print(f"   Agent ID: {agent.id}")

    # Get OpenAI client and test response
    print(f"\n💬 Testing agent response...")
    openai_client = project_client.get_openai_client()

    response = openai_client.responses.create(
        input=[{"role": "user", "content": "Tell me a one line story"}],
        extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
    )

    print(f"\n✅ Response received!")
    print(f"\n📝 Story: {response.output_text}")

    print("\n" + "="*60)
    print("🎉 All tests passed! Your Azure AI Foundry setup is working!")
    print("="*60)

except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"\n💡 Troubleshooting tips:")
    print(f"   1. Verify your .env file has the correct AZURE_AI_PROJECT_ENDPOINT")
    print(f"   2. Make sure you're logged in: az login")
    print(f"   3. Check that your Azure account has access to the project")
    print(f"   4. Verify the model deployment name exists in Azure AI Foundry")
    raise
