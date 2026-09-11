namespace NesNewLife.SMB2
{
    public static class CampaignCatalog
    {
        public const int StageCount = 3;

        public static string SceneForStage(int stageNumber)
        {
            switch (stageNumber)
            {
                case 1: return "SMB2_Stage_01";
                case 2: return "SMB2_Stage_02";
                case 3: return "SMB2_Stage_03";
                default: return "SMB2_Stage_01";
            }
        }

        public static string DisplayNameForStage(int stageNumber)
        {
            switch (stageNumber)
            {
                case 1: return "1-1 Verdant Approach";
                case 2: return "1-2 Buried Passage";
                case 3: return "1-3 Crimson Keep";
                default: return $"Stage {stageNumber}";
            }
        }
    }

    public static class CampaignRuntimeBridge
    {
        public static bool ResumeAfterSceneTransition { get; set; }
    }
}
