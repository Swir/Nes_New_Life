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

            Rect panel = new Rect(18, 18, 470, 176);
            GUI.DrawTexture(panel, panelTexture);
            GUI.Label(new Rect(34, 28, 430, 30), "NES NEW LIFE #001", titleStyle);
            GUI.Label(new Rect(34, 62, 430, 26), $"{tuning.DisplayName}   HP: {(health != null ? health.CurrentHealth : 0)}/{(health != null ? health.MaxHealth : 0)}", textStyle);
            GUI.Label(new Rect(34, 88, 430, 26), $"Lives: {gm.Lives}   Keys: {(inventory != null ? inventory.Keys : 0)}   Score: {gm.Score:000000}", textStyle);
            GUI.Label(new Rect(34, 114, 430, 26), $"Best: {gm.BestScore:000000}   Clears: {gm.Clears}   Deaths: {gm.TotalDeaths}", textStyle);
            GUI.Label(new Rect(34, 142, 430, 30), "A/D Move • Space Jump • Shift Carry • ↑/W Door • P Pause", textStyle);

            if (gm.HasNotification)
            {
                float width = Mathf.Min(560f, Screen.width - 40f);
                Rect notification = new Rect((Screen.width - width) * 0.5f, 22f, width, 58f);
                GUI.DrawTexture(notification, panelTexture);
                GUI.Label(notification, gm.NotificationText, messageStyle);
            }

            if (gm.State == RunState.Playing)
                return;

            Rect overlay = new Rect(Screen.width * 0.5f - 280, Screen.height * 0.5f - 120, 560, 240);
            GUI.DrawTexture(overlay, panelTexture);

            string message;
            if (gm.State == RunState.Paused)
                message = "PAUSED\n\nPress P or Esc to continue";
            else if (gm.State == RunState.Won)
                message = $"LEVEL COMPLETE!\nScore: {gm.Score:000000}   Best: {gm.BestScore:000000}\nClears: {gm.Clears}\n\nPress R for another run";
            else
                message = $"GAME OVER\nTotal deaths: {gm.TotalDeaths}\n\nPress R to restart";

            GUI.Label(overlay, message, centerStyle);
        }

        private void DrawCharacterSelect(GameManager gm)
        {
            float width = Mathf.Min(780f, Screen.width - 30f);
            float left = (Screen.width - width) * 0.5f;
            Rect panel = new Rect(left, Mathf.Max(20f, Screen.height * 0.5f - 245f), width, 490f);
            GUI.DrawTexture(panel, panelTexture);

            GUI.Label(new Rect(left + 20, panel.y + 22, width - 40, 50), "CHOOSE YOUR CHARACTER", centerStyle);

            string saveLine = gm.HasSave
                ? $"C = continue as {CharacterTuning.For(CampaignSave.LastCharacter).DisplayName}   •   N = reset progress\nBest {gm.BestScore:000000}   Clears {gm.Clears}   Deaths {gm.TotalDeaths}"
                : "No save yet — choose 1, 2, 3 or 4 to begin";
            GUI.Label(new Rect(left + 25, panel.y + 75, width - 50, 58), saveLine, selectStyle);

            string choices =
                "1  MARIO\nBalanced speed, jump and throw\n\n" +
                "2  LUIGI\nHigher jump, looser air control\n\n" +
                "3  PEACH\nHold jump while falling to float\n\n" +
                "4  TOAD\nFast movement and strongest throw";

            GUI.Label(new Rect(left + 45, panel.y + 145, width - 90, 315), choices, selectStyle);
        }

        private void OnDestroy()
        {
            if (panelTexture != null)
                Destroy(panelTexture);
        }
    }
}
