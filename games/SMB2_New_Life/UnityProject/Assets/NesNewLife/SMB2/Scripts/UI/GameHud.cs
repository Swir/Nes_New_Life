using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class GameHud : MonoBehaviour
    {
        private GUIStyle titleStyle;
        private GUIStyle textStyle;
        private GUIStyle centerStyle;
        private GUIStyle selectStyle;
        private GUIStyle messageStyle;
        private Texture2D panelTexture;

        private void Awake()
        {
            panelTexture = new Texture2D(1, 1);
            panelTexture.SetPixel(0, 0, new Color(0.03f, 0.05f, 0.08f, 0.90f));
            panelTexture.Apply();
        }

        private void EnsureStyles()
        {
            if (textStyle != null)
                return;

            textStyle = new GUIStyle(GUI.skin.label);
            textStyle.fontSize = 18;
            textStyle.normal.textColor = Color.white;

            titleStyle = new GUIStyle(textStyle);
            titleStyle.fontSize = 24;
            titleStyle.fontStyle = FontStyle.Bold;

            centerStyle = new GUIStyle(titleStyle);
            centerStyle.alignment = TextAnchor.MiddleCenter;
            centerStyle.fontSize = 34;
            centerStyle.wordWrap = true;

            selectStyle = new GUIStyle(textStyle);
            selectStyle.alignment = TextAnchor.MiddleCenter;
            selectStyle.fontSize = 20;
            selectStyle.wordWrap = true;

            messageStyle = new GUIStyle(titleStyle);
            messageStyle.alignment = TextAnchor.MiddleCenter;
            messageStyle.fontSize = 22;
            messageStyle.wordWrap = true;
        }

        private void OnGUI()
        {
            EnsureStyles();
            GameManager gm = GameManager.Instance;
            if (gm == null)
                return;

            if (gm.State == RunState.CharacterSelect)
            {
                DrawCharacterSelect(gm);
                return;
            }

            PlayerHealth health = FindFirstObjectByType<PlayerHealth>();
            PlayerInventory inventory = FindFirstObjectByType<PlayerInventory>();
            CharacterTuning tuning = CharacterTuning.For(gm.SelectedCharacter);
            int world = CampaignCatalog.WorldForStage(gm.StageNumber);
            int level = CampaignCatalog.LevelForStage(gm.StageNumber);

            Rect panel = new Rect(18, 18, 520, 226);
            GUI.DrawTexture(panel, panelTexture);
            GUI.Label(new Rect(34, 28, 475, 30), "NES NEW LIFE #001", titleStyle);
            GUI.Label(new Rect(34, 58, 475, 26), $"WORLD {world}-{level}   {gm.StageName}", textStyle);
            GUI.Label(new Rect(34, 84, 475, 26), $"Campaign stage {gm.StageNumber}/{CampaignCatalog.StageCount}   World {world}/{CampaignCatalog.WorldCount}", textStyle);
            GUI.Label(new Rect(34, 110, 475, 26), $"{tuning.DisplayName}   HP: {(health != null ? health.CurrentHealth : 0)}/{(health != null ? health.MaxHealth : 0)}", textStyle);
            GUI.Label(new Rect(34, 136, 475, 26), $"Lives: {gm.Lives}   Keys: {(inventory != null ? inventory.Keys : 0)}   Score: {gm.Score:000000}", textStyle);
            GUI.Label(new Rect(34, 162, 475, 26), $"Best: {gm.BestScore:000000}   Clears: {gm.Clears}   Deaths: {gm.TotalDeaths}", textStyle);
            GUI.Label(new Rect(34, 190, 475, 30), "A/D Move • Space Jump • Shift Carry • ↑/W Door • P Pause", textStyle);

            if (gm.HasNotification)
            {
                float width = Mathf.Min(560f, Screen.width - 40f);
                Rect notification = new Rect((Screen.width - width) * 0.5f, 22f, width, 58f);
                GUI.DrawTexture(notification, panelTexture);
                GUI.Label(notification, gm.NotificationText, messageStyle);
            }

            if (gm.State == RunState.Playing)
                return;

            Rect overlay = new Rect(Screen.width * 0.5f - 290, Screen.height * 0.5f - 130, 580, 260);
            GUI.DrawTexture(overlay, panelTexture);

            string message;
            if (gm.State == RunState.Paused)
                message = $"PAUSED\n{gm.StageName}\n\nPress P or Esc to continue";
            else if (gm.State == RunState.Won)
                message = $"7-WORLD CAMPAIGN COMPLETE!\nScore: {gm.Score:000000}   Best: {gm.BestScore:000000}\nClears: {gm.Clears}\n\nPress R for a new campaign";
            else
                message = $"GAME OVER\nReached: {gm.StageName}\nTotal deaths: {gm.TotalDeaths}\n\nPress R to restart campaign";

            GUI.Label(overlay, message, centerStyle);
        }

        private void DrawCharacterSelect(GameManager gm)
        {
            float width = Mathf.Min(840f, Screen.width - 30f);
            float left = (Screen.width - width) * 0.5f;
            Rect panel = new Rect(left, Mathf.Max(20f, Screen.height * 0.5f - 285f), width, 570f);
            GUI.DrawTexture(panel, panelTexture);

            GUI.Label(new Rect(left + 20, panel.y + 18, width - 40, 50), "CHOOSE YOUR CHARACTER", centerStyle);

            CampaignStageSelector selector = FindFirstObjectByType<CampaignStageSelector>();
            string stageSelectLine = selector != null && gm.HasSave
                ? $"Stage select: {selector.SelectedStageName}   •   Q/E change   •   Enter start unlocked stage"
                : string.Empty;

            string saveLine = CampaignSave.CampaignActive
                ? $"C = continue {CampaignCatalog.DisplayNameForStage(CampaignSave.CurrentStage)} as {CharacterTuning.For(CampaignSave.LastCharacter).DisplayName}\nRun score {CampaignSave.RunScore:000000}   Lives {CampaignSave.RunLives}   Highest unlocked {CampaignCatalog.ShortNameForStage(gm.HighestUnlockedStage)}"
                : gm.HasSave
                    ? $"Progress saved • Highest unlocked {CampaignCatalog.ShortNameForStage(gm.HighestUnlockedStage)} • N = reset all progress\nBest {gm.BestScore:000000}   Clears {gm.Clears}   Deaths {gm.TotalDeaths}"
                    : "No save yet — choose 1, 2, 3 or 4 to begin at World 1-1";
            GUI.Label(new Rect(left + 25, panel.y + 72, width - 50, 78), saveLine, selectStyle);

            if (!string.IsNullOrEmpty(stageSelectLine))
                GUI.Label(new Rect(left + 25, panel.y + 145, width - 50, 44), stageSelectLine, selectStyle);

            string choices =
                "1  MARIO\nBalanced speed, jump and throw\n\n" +
                "2  LUIGI\nHigher jump, looser air control\n\n" +
                "3  PEACH\nHold jump while falling to float\n\n" +
                "4  TOAD\nFast movement and strongest throw";

            GUI.Label(new Rect(left + 45, panel.y + 205, width - 90, 315), choices, selectStyle);
            GUI.Label(new Rect(left + 25, panel.y + 520, width - 50, 30), $"Campaign: {CampaignCatalog.WorldCount} worlds • {CampaignCatalog.StageCount} stages", selectStyle);
        }

        private void OnDestroy()
        {
            if (panelTexture != null)
                Destroy(panelTexture);
        }
    }
}
