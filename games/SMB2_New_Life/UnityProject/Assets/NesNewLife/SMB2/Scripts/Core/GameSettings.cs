using UnityEngine;

namespace NesNewLife.SMB2
{
    public static class GameSettings
    {
        private const string Prefix = "NesNewLife.SMB2.Settings.";
        private const string MasterVolumeKey = Prefix + "MasterVolume";
        private const string HudScaleKey = Prefix + "HudScale";
        private const string ReducedFlashKey = Prefix + "ReducedFlash";
        private const string AssistHealthKey = Prefix + "AssistHealth";
        private const string ExtraLivesKey = Prefix + "ExtraLives";

        public static float MasterVolume
        {
            get => Mathf.Clamp01(PlayerPrefs.GetFloat(MasterVolumeKey, 0.85f));
            set
            {
                PlayerPrefs.SetFloat(MasterVolumeKey, Mathf.Clamp01(value));
                PlayerPrefs.Save();
                ApplyRuntime();
            }
        }

        public static float HudScale
        {
            get => Mathf.Clamp(PlayerPrefs.GetFloat(HudScaleKey, 1f), 0.8f, 1.5f);
            set
            {
                PlayerPrefs.SetFloat(HudScaleKey, Mathf.Clamp(value, 0.8f, 1.5f));
                PlayerPrefs.Save();
            }
        }

        public static bool ReducedFlash
        {
            get => PlayerPrefs.GetInt(ReducedFlashKey, 0) == 1;
            set
            {
                PlayerPrefs.SetInt(ReducedFlashKey, value ? 1 : 0);
                PlayerPrefs.Save();
            }
        }

        public static bool AssistHealth
        {
            get => PlayerPrefs.GetInt(AssistHealthKey, 0) == 1;
            set
            {
                PlayerPrefs.SetInt(AssistHealthKey, value ? 1 : 0);
                PlayerPrefs.Save();
            }
        }

        public static bool ExtraLives
        {
            get => PlayerPrefs.GetInt(ExtraLivesKey, 0) == 1;
            set
            {
                PlayerPrefs.SetInt(ExtraLivesKey, value ? 1 : 0);
                PlayerPrefs.Save();
            }
        }

        public static int StartingLives(int normalLives)
        {
            return ExtraLives ? Mathf.Max(normalLives, 5) : normalLives;
        }

        public static int HealthBonus => AssistHealth ? 2 : 0;

        public static void ApplyRuntime()
        {
            AudioListener.volume = MasterVolume;
        }

        public static void ResetToDefaults()
        {
            PlayerPrefs.DeleteKey(MasterVolumeKey);
            PlayerPrefs.DeleteKey(HudScaleKey);
            PlayerPrefs.DeleteKey(ReducedFlashKey);
            PlayerPrefs.DeleteKey(AssistHealthKey);
            PlayerPrefs.DeleteKey(ExtraLivesKey);
            PlayerPrefs.Save();
            ApplyRuntime();
        }
    }
}
