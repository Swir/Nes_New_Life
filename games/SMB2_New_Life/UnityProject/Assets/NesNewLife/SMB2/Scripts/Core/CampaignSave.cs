using UnityEngine;

namespace NesNewLife.SMB2
{
    public static class CampaignSave
    {
        private const string Prefix = "NesNewLife.SMB2.";
        private const string BestScoreKey = Prefix + "BestScore";
        private const string ClearsKey = Prefix + "Clears";
        private const string DeathsKey = Prefix + "Deaths";
        private const string CharacterKey = Prefix + "Character";
        private const string HasSaveKey = Prefix + "HasSave";
        private const string CampaignActiveKey = Prefix + "CampaignActive";
        private const string CurrentStageKey = Prefix + "CurrentStage";
        private const string HighestStageKey = Prefix + "HighestStage";
        private const string RunScoreKey = Prefix + "RunScore";
        private const string RunLivesKey = Prefix + "RunLives";

        public static bool HasSave => PlayerPrefs.GetInt(HasSaveKey, 0) == 1;
        public static bool CampaignActive => PlayerPrefs.GetInt(CampaignActiveKey, 0) == 1;
        public static int BestScore => Mathf.Max(0, PlayerPrefs.GetInt(BestScoreKey, 0));
        public static int Clears => Mathf.Max(0, PlayerPrefs.GetInt(ClearsKey, 0));
        public static int Deaths => Mathf.Max(0, PlayerPrefs.GetInt(DeathsKey, 0));
        public static int CurrentStage => Mathf.Max(1, PlayerPrefs.GetInt(CurrentStageKey, 1));
        public static int HighestUnlockedStage => Mathf.Max(1, PlayerPrefs.GetInt(HighestStageKey, 1));
        public static int RunScore => Mathf.Max(0, PlayerPrefs.GetInt(RunScoreKey, 0));
        public static int RunLives => Mathf.Max(0, PlayerPrefs.GetInt(RunLivesKey, 3));

        public static CharacterType LastCharacter
        {
            get
            {
                int value = PlayerPrefs.GetInt(CharacterKey, (int)CharacterType.Mario);
                return System.Enum.IsDefined(typeof(CharacterType), value)
                    ? (CharacterType)value
                    : CharacterType.Mario;
            }
        }

        public static void BeginCampaign(CharacterType character, int stageNumber, int lives = 3, int score = 0)
        {
            PlayerPrefs.SetInt(HasSaveKey, 1);
            PlayerPrefs.SetInt(CampaignActiveKey, 1);
            PlayerPrefs.SetInt(CharacterKey, (int)character);
            PlayerPrefs.SetInt(CurrentStageKey, Mathf.Max(1, stageNumber));
            PlayerPrefs.SetInt(HighestStageKey, Mathf.Max(HighestUnlockedStage, stageNumber));
            PlayerPrefs.SetInt(RunLivesKey, Mathf.Max(1, lives));
            PlayerPrefs.SetInt(RunScoreKey, Mathf.Max(0, score));
            PlayerPrefs.Save();
        }

        public static void SaveRun(CharacterType character, int stageNumber, int lives, int score)
        {
            PlayerPrefs.SetInt(HasSaveKey, 1);
            PlayerPrefs.SetInt(CampaignActiveKey, 1);
            PlayerPrefs.SetInt(CharacterKey, (int)character);
            PlayerPrefs.SetInt(CurrentStageKey, Mathf.Max(1, stageNumber));
            PlayerPrefs.SetInt(HighestStageKey, Mathf.Max(HighestUnlockedStage, stageNumber));
            PlayerPrefs.SetInt(RunLivesKey, Mathf.Max(0, lives));
            PlayerPrefs.SetInt(RunScoreKey, Mathf.Max(0, score));
            PlayerPrefs.Save();
        }

        public static void MarkStarted(CharacterType character)
        {
            BeginCampaign(character, CurrentStage, Mathf.Max(1, RunLives), RunScore);
        }

        public static void RecordDeath()
        {
            PlayerPrefs.SetInt(HasSaveKey, 1);
            PlayerPrefs.SetInt(DeathsKey, Deaths + 1);
            PlayerPrefs.Save();
        }

        public static void RecordClear(int score, CharacterType character)
        {
            PlayerPrefs.SetInt(HasSaveKey, 1);
            PlayerPrefs.SetInt(CampaignActiveKey, 0);
            PlayerPrefs.SetInt(CharacterKey, (int)character);
            PlayerPrefs.SetInt(ClearsKey, Clears + 1);
            PlayerPrefs.SetInt(CurrentStageKey, 1);
            PlayerPrefs.SetInt(RunLivesKey, 3);
            PlayerPrefs.SetInt(RunScoreKey, 0);
            if (score > BestScore)
                PlayerPrefs.SetInt(BestScoreKey, score);
            PlayerPrefs.Save();
        }

        public static void AbandonCampaign()
        {
            PlayerPrefs.SetInt(CampaignActiveKey, 0);
            PlayerPrefs.SetInt(CurrentStageKey, 1);
            PlayerPrefs.SetInt(RunLivesKey, 3);
            PlayerPrefs.SetInt(RunScoreKey, 0);
            PlayerPrefs.Save();
        }

        public static void ResetProgress()
        {
            PlayerPrefs.DeleteKey(BestScoreKey);
            PlayerPrefs.DeleteKey(ClearsKey);
            PlayerPrefs.DeleteKey(DeathsKey);
            PlayerPrefs.DeleteKey(CharacterKey);
            PlayerPrefs.DeleteKey(HasSaveKey);
            PlayerPrefs.DeleteKey(CampaignActiveKey);
            PlayerPrefs.DeleteKey(CurrentStageKey);
            PlayerPrefs.DeleteKey(HighestStageKey);
            PlayerPrefs.DeleteKey(RunScoreKey);
            PlayerPrefs.DeleteKey(RunLivesKey);
            PlayerPrefs.Save();
        }
    }
}
