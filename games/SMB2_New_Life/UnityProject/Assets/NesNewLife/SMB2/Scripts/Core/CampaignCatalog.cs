namespace NesNewLife.SMB2
{
    public static class CampaignCatalog
    {
        public const int StageCount = 20;
        public const int WorldCount = 7;

        private static readonly int[] WorldFirstStage = { 1, 4, 7, 10, 13, 16, 19 };
        private static readonly int[] WorldStageCounts = { 3, 3, 3, 3, 3, 3, 2 };

        private static readonly string[] StageTitles =
        {
            "Verdant Approach", "Buried Passage", "Crimson Keep",
            "Windcut Terrace", "Rootbound Depths", "Moonlit Bastion",
            "Sunken Garden", "Falling Columns", "Ember Citadel",
            "Cloudstep Rise", "Hollow Reservoir", "Storm Gate",
            "Twilight Orchard", "Clockwork Cavern", "Obsidian Hall",
            "Starfall Ascent", "Silent Underway", "Iron Crown",
            "Final Approach", "Dreambreaker Spire"
        };

        public static string SceneForStage(int stageNumber)
        {
            int stage = ClampStage(stageNumber);
            return $"SMB2_Stage_{stage:00}";
        }

        public static string DisplayNameForStage(int stageNumber)
        {
            int stage = ClampStage(stageNumber);
            GetWorldAndLevel(stage, out int world, out int level);
            return $"{world}-{level} {StageTitles[stage - 1]}";
        }

        public static string ShortNameForStage(int stageNumber)
        {
            int stage = ClampStage(stageNumber);
            GetWorldAndLevel(stage, out int world, out int level);
            return $"{world}-{level}";
        }

        public static int WorldForStage(int stageNumber)
        {
            GetWorldAndLevel(ClampStage(stageNumber), out int world, out _);
            return world;
        }

        public static int LevelForStage(int stageNumber)
        {
            GetWorldAndLevel(ClampStage(stageNumber), out _, out int level);
            return level;
        }

        public static int FirstStageForWorld(int worldNumber)
        {
            int world = ClampWorld(worldNumber);
            return WorldFirstStage[world - 1];
        }

        public static int StageCountForWorld(int worldNumber)
        {
            int world = ClampWorld(worldNumber);
            return WorldStageCounts[world - 1];
        }

        public static int LastStageForWorld(int worldNumber)
        {
            int world = ClampWorld(worldNumber);
            return FirstStageForWorld(world) + StageCountForWorld(world) - 1;
        }

        public static bool IsWorldFinale(int stageNumber)
        {
            int stage = ClampStage(stageNumber);
            return stage == LastStageForWorld(WorldForStage(stage));
        }

        public static int ClampStage(int stageNumber)
        {
            return UnityEngine.Mathf.Clamp(stageNumber, 1, StageCount);
        }

        private static int ClampWorld(int worldNumber)
        {
            return UnityEngine.Mathf.Clamp(worldNumber, 1, WorldCount);
        }

        private static void GetWorldAndLevel(int stageNumber, out int world, out int level)
        {
            for (int i = 0; i < WorldCount; i++)
            {
                int first = WorldFirstStage[i];
                int count = WorldStageCounts[i];
                if (stageNumber >= first && stageNumber < first + count)
                {
                    world = i + 1;
                    level = stageNumber - first + 1;
                    return;
                }
            }

            world = WorldCount;
            level = WorldStageCounts[WorldCount - 1];
        }
    }

    public static class CampaignRuntimeBridge
    {
        public static bool ResumeAfterSceneTransition { get; set; }
    }
}
