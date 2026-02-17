from typing import List
from crewai.flow.flow import Flow, listen, start, router, and_, or_
from crewai import LLM
from pydantic import BaseModel

from research_crew import ResearchCrew
from seo_crew import SeoCrew
from virality_crew import ViralityCrew


class BlogPost(BaseModel):
    title: str
    subtitle: str
    sections: List[str]

class Tweet(BaseModel):
    content: str
    hashtags: str

class LinkedInPost(BaseModel):
    hook: str
    content: str
    call_to_action: str

class Score(BaseModel):
    score: int = 0
    reason: str = ""

class ContentPipelineState(BaseModel):

    # Inputs
    content_type: str = ""
    topic: str = ""

    # Internal
    max_length: int = 0
    research: str = ""
    score: Score | None = None

    # Content
    blog_post: BlogPost | None = None
    tweet: Tweet | None = None
    linkedin_post: LinkedInPost | None = None


class ContentPipelineFlow(Flow[ContentPipelineState]):

    @start()
    def init_content_pipeline(self):

        if self.state.content_type not in ["blog_post", "tweet", "linkedin_post"]:
            raise ValueError("Invalid content type. Must be 'blog_post', 'tweet', or 'linkedin_post'.")

        if self.state.topic == "":
            raise ValueError("The topic cannot be empty.")

        if self.state.content_type == "tweet":
            self.state.max_length = 100
        elif self.state.content_type == "linkedin_post":
            self.state.max_length = 500
        elif self.state.content_type == "blog_post":
            self.state.max_length = 800

    @listen(init_content_pipeline)
    def conduct_research(self):

        result = (
            ResearchCrew(topic=self.state.topic)
            .crew()
            .kickoff(
            )
        )

        self.state.research = result["research"]

    @router(conduct_research)
    def conduct_research_router(self):
        content_type = self.state.content_type

        if content_type == "blog_post":
            return "generate_blog_post"
        elif content_type == "tweet":
            return "generate_tweet"
        elif content_type == "linkedin_post":
            return "generate_linkedin_post"

    @listen(or_("generate_blog_post", "regenerate_blog_post"))
    def handle_generate_blog_post(self):

        blog_post = self.state.blog_post

        llm = LLM(model="gpt-5-nano", response_format=BlogPost)

        if blog_post is None:
            result = llm.call(
                f"""
                Using the following research, create a blog post on the topic {self.state.topic}. The blog post should be well-structured and include a title, subtitle, and several sections that cover different aspects of the topic. The content should be concise and directly related to the research provided. Ensure that the blog post is engaging and informative, making use of the key insights and information gathered during the research phase.
                
                <research>
                {self.state.research}
                </research>
                """,
            )
        else:
            result = llm.call(
                f"""
                The following is a blog post that was generated based on research on the topic {self.state.topic}. The blog post includes a title, subtitle, and several sections that cover different aspects of the topic. However, it may not be perfect and may require improvements to better capture the key insights from the research and to be more engaging and informative. Please review the blog post and make necessary improvements to enhance its quality, ensuring that it is concise, directly related to the research provided, and effectively communicates the key insights in an engaging manner.
                
                <research>
                {self.state.research}
                </research>

                <blog_post>
                {blog_post.model_dump_json()}
                </blog_post>
                """,
            )
        self.state.blog_post = result

    @listen(or_("generate_tweet", "regenerate_tweet"))
    def handle_generate_tweet(self):

        tweet = self.state.tweet
        llm = LLM(model="gpt-5-nano", response_format=Tweet)
        if tweet is None:
            result = llm.call(
                f"""
                Using the following research, create a tweet on the topic {self.state.topic}. The tweet should be concise and engaging, capturing the essence of the topic in a way that resonates with the audience. It should include relevant hashtags to increase visibility and engagement. Ensure that the content is directly related to the research provided and effectively communicates the key insights in a compelling manner.
                
                <research>
                {self.state.research}
                </research>
                """,
            )
        else:
            result = llm.call(
                f"""
                The following is a tweet that was generated based on research on the topic {self.state.topic}. The tweet is concise and engaging, capturing the essence of the topic in a way that resonates with the audience. It includes relevant hashtags to increase visibility and engagement. However, it may not be perfect and may require improvements to better capture the key insights from the research and to be more compelling. Please review the tweet and make necessary improvements to enhance its quality, ensuring that it is concise, directly related to the research provided, and effectively communicates the key insights in a compelling manner.
                
                <research>
                {self.state.research}
                </research>

                <tweet>
                {tweet.model_dump_json()}
                </tweet>
                """,
            )
        self.state.tweet = result

    @listen(or_("generate_linkedin_post", "regenerate_linkedin_post"))
    def handle_generate_linkedin_post(self):
        linkedin_post = self.state.linkedin_post

        llm = LLM(model="gpt-5-nano", response_format=LinkedInPost)

        if linkedin_post is None:
            result = llm.call(
                f"""
                Using the following research, create a LinkedIn post on the topic {self.state.topic}. The LinkedIn post should include a compelling hook to grab the reader's attention, followed by informative content that provides value to the audience. It should conclude with a strong call to action that encourages engagement, such as asking readers to share their thoughts or visit a website for more information. Ensure that the content is directly related to the research provided and effectively communicates the key insights in a professional and engaging manner.
                
                <research>
                {self.state.research}
                </research>
                """,
            )
        else:
            result = llm.call(
                f"""
                The following is a LinkedIn post that was generated based on research on the topic {self.state.topic}. The LinkedIn post includes a compelling hook to grab the reader's attention, followed by informative content that provides value to the audience. It concludes with a strong call to action that encourages engagement, such as asking readers to share their thoughts or visit a website for more information. However, it may not be perfect and may require improvements to better capture the key insights from the research and to be more professional and engaging. Please review the LinkedIn post and make necessary improvements to enhance its quality, ensuring that it is directly related to the research provided and effectively communicates the key insights in a professional and engaging manner.
                
                <research>
                {self.state.research}
                </research>

                <linkedin_post>
                {linkedin_post.model_dump_json()}
                </linkedin_post>
                """,
            )
        self.state.linkedin_post = result

    @listen(handle_generate_blog_post)
    def check_seo(self):

        result = (
            SeoCrew()
            .crew()
            .kickoff(
                inputs={
                    "blog_post": self.state.blog_post.model_dump_json(),
                    "topic": self.state.topic,
                }
            )
        )
        self.state.score = result.pydantic

    @listen(or_(handle_generate_tweet, handle_generate_linkedin_post))
    def check_virality(self):
        result = (
            ViralityCrew()
            .crew()
            .kickoff(
                inputs={
                    "content_type": self.state.content_type,
                    "content": self.state.tweet.model_dump_json() if self.state.content_type == "tweet" else self.state.linkedin_post.model_dump_json(),
                    "topic": self.state.topic,
                }
            )
        )
        self.state.score = result.pydantic

    @router(or_(check_seo, check_virality))
    def score_router(self):
        content_type = self.state.content_type
        score = self.state.score

        if score.score >= 5:
            return "check_passed"
        else:
            if content_type == "blog_post":
                return "regenerate_blog_post"
            elif content_type == "tweet":
                return "regenerate_tweet"
            elif content_type == "linkedin_post":
                return "regenerate_linkedin_post"

    @listen("check_passed")
    def finalize_content(self):
        """Content has passed the quality check and is finalized."""
        print("Finalizing Content!!!")

        if self.state.content_type == "blog_post":
            print(f"📝 Blog Post: {self.state.blog_post.title}")
            print(f"🔍 SEO Score: {self.state.score.score}/10")
        elif self.state.content_type == "tweet":
            print(f"🐦 Tweet: {self.state.tweet.content}")
            print(f"🚀 Virality Score: {self.state.score.score}/10")
        elif self.state.content_type == "linkedin_post":
            print(f"💼 LinkedIn: {self.state.linkedin_post.hook}")
            print(f"🚀 Virality Score: {self.state.score.score}/10")

        print("✅ Content ready for publication!")
        return (
            self.state.linkedin_post
            if self.state.content_type == "linkedin_post"
            else (
                self.state.tweet
                if self.state.content_type == "tweet"
                else self.state.blog_post
            ))


flow = ContentPipelineFlow()
flow.kickoff(inputs={"content_type": "tweet", "topic": "The Future of AI in Content Creation"})
flow.plot("content_pipeline_flow.html")
