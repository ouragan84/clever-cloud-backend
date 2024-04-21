import requests
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Protocol, Model, Context, Agent

# Define the PDF Summarization Request model
class PDFSummarizationRequest(Model):
    url: str

# Define the protocol for PDF Summarization
pdf_summarization_protocol = Protocol("PDF Summarization")

agent = Agent(seed='myownpasswordfornow')

# Global counter for the number of summarizations
summarization_count = 0

def upload_pdf(url, ctx):
    """Uploads a PDF from a URL and returns the document ID."""
    endpoint = "https://pdf.ai/api/v1/upload/url"
    headers = {
        "X-API-Key": 'eyJhbGciOiJSUzI1NiJ9.eyJleHAiOjE3MTYyNDk3ODIsImlhdCI6MTcxMzY1Nzc4MiwiaXNzIjoiZmV0Y2guYWkiLCJqdGkiOiJlNDA0MmU1Nzc3MzM4YWNhZWI0YWRhYzMiLCJzY29wZSI6ImF2OnJvIiwic3ViIjoiMjE3YzMwNzcxYTRiMmI2NGZlZWU3MzM4MTY0NWRjZmM5OGY5YmM3OWI0NmNhYzcxIn0.O8AKGCNuos-USRhD9XlZA3JOFtNWD3HXTCybR6U3tk9G4s03LtRKIIkQIFH9ie2udldCC_0n2Cc_h7XIKben5T759djJl2zQEdacA_M1rk5WuN-gDDVNbwV_amvczsaPsfj2lyzWlSVwbzrE2FeM8tNx-3Dg0p1wx2AiG2fokZBJcEdje95faGQkqLlkpFNiZDPpNTu2FxQeD4jAzzTcJfTOhnImHGHfjkFwKMzpwTzQW39nUQ1yWsgP2Cm2TqamSY3eJp8KcVZYgTYrJ6ye_cp-mthMj05kEnP6UyKiFSclDfYFAOmVyNUxzDWIf6rMyhA-HnBu6fc0MFTvaeh2GA'
    }
    payload = {
        "url": url,
        "isPrivate": False,  # Assuming the file is not private
        "ocr": False          # Enabling OCR
    }
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("docId")
    except requests.RequestException as e:
        ctx.logger.info(f"Error during PDF upload: {e}")
        return None

def summarize_pdf(doc_id, ctx):
    """Summarizes the uploaded PDF and returns the summary."""
    endpoint = "https://pdf.ai/api/v1/summary"
    headers = {
        "X-API-Key": 'eyJhbGciOiJSUzI1NiJ9.eyJleHAiOjE3MTYyNDk3ODIsImlhdCI6MTcxMzY1Nzc4MiwiaXNzIjoiZmV0Y2guYWkiLCJqdGkiOiJlNDA0MmU1Nzc3MzM4YWNhZWI0YWRhYzMiLCJzY29wZSI6ImF2OnJvIiwic3ViIjoiMjE3YzMwNzcxYTRiMmI2NGZlZWU3MzM4MTY0NWRjZmM5OGY5YmM3OWI0NmNhYzcxIn0.O8AKGCNuos-USRhD9XlZA3JOFtNWD3HXTCybR6U3tk9G4s03LtRKIIkQIFH9ie2udldCC_0n2Cc_h7XIKben5T759djJl2zQEdacA_M1rk5WuN-gDDVNbwV_amvczsaPsfj2lyzWlSVwbzrE2FeM8tNx-3Dg0p1wx2AiG2fokZBJcEdje95faGQkqLlkpFNiZDPpNTu2FxQeD4jAzzTcJfTOhnImHGHfjkFwKMzpwTzQW39nUQ1yWsgP2Cm2TqamSY3eJp8KcVZYgTYrJ6ye_cp-mthMj05kEnP6UyKiFSclDfYFAOmVyNUxzDWIf6rMyhA-HnBu6fc0MFTvaeh2GA'
    }
    payload = {
        "docId": doc_id,
        "language": "english"
    }
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        ctx.logger.info(f"Error during PDF summarization: {e}")
        return None

def delete_pdf(doc_id, ctx):
    """Deletes the uploaded PDF."""
    endpoint = "https://pdf.ai/api/v1/delete"
    headers = {
        "X-API-Key": 'eyJhbGciOiJSUzI1NiJ9.eyJleHAiOjE3MTYyNDk3ODIsImlhdCI6MTcxMzY1Nzc4MiwiaXNzIjoiZmV0Y2guYWkiLCJqdGkiOiJlNDA0MmU1Nzc3MzM4YWNhZWI0YWRhYzMiLCJzY29wZSI6ImF2OnJvIiwic3ViIjoiMjE3YzMwNzcxYTRiMmI2NGZlZWU3MzM4MTY0NWRjZmM5OGY5YmM3OWI0NmNhYzcxIn0.O8AKGCNuos-USRhD9XlZA3JOFtNWD3HXTCybR6U3tk9G4s03LtRKIIkQIFH9ie2udldCC_0n2Cc_h7XIKben5T759djJl2zQEdacA_M1rk5WuN-gDDVNbwV_amvczsaPsfj2lyzWlSVwbzrE2FeM8tNx-3Dg0p1wx2AiG2fokZBJcEdje95faGQkqLlkpFNiZDPpNTu2FxQeD4jAzzTcJfTOhnImHGHfjkFwKMzpwTzQW39nUQ1yWsgP2Cm2TqamSY3eJp8KcVZYgTYrJ6ye_cp-mthMj05kEnP6UyKiFSclDfYFAOmVyNUxzDWIf6rMyhA-HnBu6fc0MFTvaeh2GA'
    }
    payload = {
        "docId": doc_id
    }
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        ctx.logger.info(f"Error during PDF deletion: {e}")

# Handler for PDF Summarization requests
@pdf_summarization_protocol.on_message(model=PDFSummarizationRequest, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: PDFSummarizationRequest):
    ctx.logger.info(f"Received PDF summarization request from {sender}.")
    global summarization_count

    try:
        ctx.logger.info(f"Upload the PDF")
        # Upload the PDF
        doc_id = upload_pdf(msg.url, ctx)
        if not doc_id:
            raise Exception("Failed to upload PDF.")

        # Summarize the PDF
        ctx.logger.info(f"Summarize the PDF")
        summary = summarize_pdf(doc_id, ctx)
        if not summary:
            delete_pdf(doc_id, ctx)
            raise Exception("Failed to summarize PDF.")

        # Delete the PDF
        ctx.logger.info(f"Delete the PDF")
        delete_pdf(doc_id, ctx)

        # Increment the summarization count
        summarization_count += 1
        ctx.logger.info(f"summarization count: {summarization_count}")

        # Send the summary response
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"{summary.get('content')}",
                type=UAgentResponseType.FINAL  # Assuming FINAL indicates a successful response
            )
        )

    except requests.RequestException as req_exc:
        ctx.logger.error(f"Request failed: {req_exc}")
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"Request error: {req_exc}",
                type=UAgentResponseType.ERROR  # Assuming ERROR indicates an error response
            )
        )
    except Exception as exc:
        # Catch other general exceptions
        ctx.logger.error(f"An error occurred: {exc}")
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"Error: {exc}",
                type=UAgentResponseType.ERROR  # Assuming ERROR indicates an error response
            )
        )


# Include the PDF Summarization protocol in your agent
agent.include(pdf_summarization_protocol, publish_manifest=True)
agent.run()