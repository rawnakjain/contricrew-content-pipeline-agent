from flask import Flask, render_template, request, jsonify
from main import ContentPipelineFlow

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json
        topic = data.get("topic", "")
        content_type = data.get("content_type", "")

        if not topic or not content_type:
            return jsonify({"error": "Topic and content type are required"}), 400

        if content_type not in ["blog_post", "tweet", "linkedin_post"]:
            return jsonify({"error": "Invalid content type"}), 400

        # Run the flow
        flow = ContentPipelineFlow()
        result = flow.kickoff(inputs={"content_type": content_type, "topic": topic})

        # Prepare response based on content type
        response = {
            "content_type": content_type,
            "topic": topic,
            "score": flow.state.score.score if flow.state.score else 0,
            "reason": flow.state.score.reason if flow.state.score else "",
        }

        if content_type == "blog_post" and flow.state.blog_post:
            response["content"] = {
                "title": flow.state.blog_post.title,
                "subtitle": flow.state.blog_post.subtitle,
                "sections": flow.state.blog_post.sections,
            }
        elif content_type == "tweet" and flow.state.tweet:
            response["content"] = {
                "content": flow.state.tweet.content,
                "hashtags": flow.state.tweet.hashtags,
            }
        elif content_type == "linkedin_post" and flow.state.linkedin_post:
            response["content"] = {
                "hook": flow.state.linkedin_post.hook,
                "content": flow.state.linkedin_post.content,
                "call_to_action": flow.state.linkedin_post.call_to_action,
            }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)

