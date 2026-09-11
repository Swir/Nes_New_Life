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

        public static bool HasSave => PlayerPrefs.GetInt(HasSaveKey, 0) == 1;
        public static int BestScore => Mathf.Max(0, PlayerPrefs.GetInt(BestScoreKey, 0));
        public static int Clears => Mathf.Max(0, PlayerPrefs.GetInt(ClearsKey, 0));
        public static int Deaths => Mathf.Max(0, PlayerPrefs.GetInt(DeathsKey, 0));

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

        public static void MarkStarted(CharacterType character)
        {
            PlayerPrefs.SetInt(HasSaveKey, 1);
            PlayerPrefs.SetInt(CharacterKey, (int)character);
            PlayerPrefs.Save();
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
            PlayerPrefs.SetInt(CharacterKey, (int)character);
            PlayerPrefs.SetInt(ClearsKey, Clears + 1);
            if (score > BestScore)
                PlayerPrefs.SetInt(BestScoreKey, score);
            PlayerPrefs.Save();
        }

        public static void ResetProgress()
        {
            PlayerPrefs.DeleteKey(BestScoreKey);
            PlayerPrefs.DeleteKey(ClearsKey);
            PlayerPrefs.DeleteKey(DeathsKey);
            PlayerPrefs.DeleteKey(CharacterKey);
            PlayerPrefs.DeleteKey(HasSaveKey);
            PlayerPrefs.Save();
        }
    }
}
