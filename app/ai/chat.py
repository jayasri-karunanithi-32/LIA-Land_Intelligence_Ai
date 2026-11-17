
import logging
from collections.abc import AsyncIterator

from langchain_core.runnables import RunnableBranch, RunnableLambda

from app.ai.rag.pipeline import rag_pipeline
from app.ai.models import models
from app.ai.prompts.gemini_prompt import RAG_PROMPT_TEMPLATE

logger = logging.getLogger("lia")

NO_CONTEXT_MESSAGE = "I couldn't find related document."


class ChatService:

    def __init__(self):
        self.router = (
            RunnableLambda(self.classify_question)
            | RunnableBranch(
                (
                    lambda x: x["route"] == "land_rag",
                    RunnableLambda(self.land_rag_response)
                ),
                RunnableLambda(self.general_response)
            )
        )

    async def classify_question(self, inputs: dict) -> dict:
        """Classifies questions into land-related or general."""

        question = inputs["question"]

        classification_prompt = f"""
You are the query router for LIA (Land Intelligence AI).

Classify the following question into exactly one category:

LAND_RAG: Questions about land, property, soil, groundwater,
infrastructure, roads, agriculture, land records, geography,
villages, taluks, districts, or location-based information.

GENERAL: General knowledge, greetings, coding, mathematics,
technology, and unrelated questions.

Return ONLY one label: LAND_RAG or GENERAL.

Question: {question}
"""

        result = await models.generate(classification_prompt)

        route = (
            "land_rag"
            if "LAND_RAG" in result.upper()
            else "general"
        )

        logger.info("Question classified as: %s", route)

        return {
            "question": question,
            "route": route
        }

    async def _prepare_prompt(self, inputs: dict) -> str:
        """Prepares the appropriate prompt for streaming."""

        question = inputs["question"]

        if inputs["route"] == "land_rag":

            retrieval = await rag_pipeline.retrieve(question)

            if not retrieval["results"]:
                logger.info("No relevant documents found.")
                return ""

            context, sources = rag_pipeline.build_context(
                retrieval["results"]
            )

            prompt_value = RAG_PROMPT_TEMPLATE.invoke({
                "context": context,
                "question": question
            })

            return prompt_value.to_string()

        return f"""
You are LIA, a helpful AI assistant.

Answer the user's question clearly and accurately.
Do not claim to have retrieved information from documents.

Question: {question}

Answer:
"""

    async def land_rag_response(self, inputs: dict) -> str:
        """Processes land-related questions through RAG."""

        prompt = await self._prepare_prompt(inputs)

        if not prompt:
            return NO_CONTEXT_MESSAGE

        answer = await models.generate(prompt)

        logger.info("RAG response generated successfully.")

        return answer

    async def general_response(self, inputs: dict) -> str:
        """Answers general questions without RAG."""

        prompt = await self._prepare_prompt(inputs)

        answer = await models.generate(prompt)

        logger.info("General response generated successfully.")

        return answer

    async def chat(self, user_prompt: str) -> str:
        """Main entry point for normal responses."""

        try:
            return await self.router.ainvoke({
                "question": user_prompt
            })

        except Exception as error:
            logger.exception("Chat generation failed: %s", error)

            raise RuntimeError(
                "Unable to generate an answer from available LLM providers."
            ) from error

    async def stream_chat(self, user_prompt: str) -> AsyncIterator[str]:
        """Routes the question and streams the final LLM response."""

        try:
            # Step 1: Classify the question
            inputs = await self.classify_question({
                "question": user_prompt
            })

            # Step 2: Prepare the appropriate prompt
            prompt = await self._prepare_prompt(inputs)

            if inputs["route"] == "land_rag" and not prompt:
                yield NO_CONTEXT_MESSAGE
                return

            # Step 3: Stream response from existing fallback chain
            async for chunk in models.stream(prompt):
                yield chunk

            logger.info("Streaming response completed successfully.")

        except Exception as error:
            logger.exception("Streaming generation failed: %s", error)

            raise RuntimeError(
                "Unable to stream an answer from available LLM providers."
            ) from error


chat_service = ChatService()
