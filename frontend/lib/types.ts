export type TweetStat = { text: string; likes: number; views: number };

export type Tweet = {
  id: string;
  text: string;
  likes: number;
  views: number;
  retweets: number;
  created_at: string;
  has_media: boolean;
};

export type Topic = { label: string; tweet_count: number; share: number; tweet_ids: string[] };

export type TweetInsights = {
  total_analyzed: number;
  avg_likes: number;
  avg_views: number;
  median_likes: number;
  median_views: number;
  posts_per_week: number | null;
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
  /** Newest first. Chat answers cite these as [T1]…[Tn] by position. */
  tweets: Tweet[];
  topics: Topic[];
};

export type ProfileResponse = {
  profile: Profile;
  from_cache: boolean;
  starter_message: string;
  suggested_questions: string[];
};

export type ChatMessage = { role: "user" | "assistant"; content: string };

export type Rating = "up" | "down";
