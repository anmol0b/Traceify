export type TweetStat = { text: string; likes: number; views: number };

export type TweetInsights = {
  total_analyzed: number;
  avg_likes: number;
  avg_views: number;
  top_by_views: TweetStat[];
  top_by_likes: TweetStat[];
};

export type Profile = {
  handle: string;
  display_name: string;
  bio: string;
  location: string | null;
  website: string | null;
  profile_image_url: string | null;
  followers: number | null;
  following: number | null;
  tweet_count: number | null;
  is_verified: boolean;
  joined_at: string | null;
  public_url: string;
  recent_posts: string[];
  insights: TweetInsights;
  summary: string;
  warnings: string[];
};

export type ProfileResponse = {
  profile: Profile;
  from_cache: boolean;
  starter_message: string;
  suggested_questions: string[];
};

export type ChatMessage = { role: "user" | "assistant"; content: string };
