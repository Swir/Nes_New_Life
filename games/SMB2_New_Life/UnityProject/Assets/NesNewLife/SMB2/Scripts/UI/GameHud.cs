using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class GameHud : MonoBehaviour
    {
        private GUIStyle titleStyle;
        private GUIStyle textStyle;
        private GUIStyle centerStyle;
        private GUIStyle selectStyle;
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
        }

        private void OnGUI()
        {
            EnsureStyles();
            GameManager gm = GameManager.Instance;
            if (gm == null)
                return;

            if (gm.State == RunState.CharacterSelect)
            {
                DrawCharacterSelect();
                return;
            }

            PlayerHealth health = FindFirstObjectByType<PlayerHealth>();
            CharacterTuning tuning = CharacterTuning.For(gm.SelectedCharacter);

            Rect panel = new Rect(18, 18, 390, 142);
            GUI.DrawTexture(panel, panelTexture);
            GUI.Label(new Rect(34, 28, 350, 30), "NES NEW LIFE #001", titleStyle);
            GUI.Label(new Rect(34, 62, 350, 26), $"{tuning.DisplayName}   HP: {(health != null ? health.CurrentHealth : 0)}/{(health != null ? health.MaxHealth : 0)}", textStyle);
            GUI.Label(new Rect(34, 88, 350, 26), $"Lives: {gm.Lives}   Score: {gm.Score:000000}", textStyle);
            GUI.Label(new Rect(34, 116, 350, 30), "A/D Move • Space Jump • Shift Carry • P Pause", textStyle);

            if (gm.State == RunState.Playing)
                return;

            Rect overlay = new Rect(Screen.width * 0.5f - 280, Screen.height * 0.5f - 110, 560, 220);
            GUI.DrawTexture(overlay, panelTexture);

            string message;
            if (gm.State == RunState.Paused)
                message = "PAUSED\n\nPress P or Esc to continue";
            else if (gm.State == RunState.Won)
                message = $"LEVEL COMPLETE!\nScore: {gm.Score:000000}\n\nPress R to replay";
            else
                message = "GAME OVER\n\nPress R to restart";

            GUI.Label(overlay, message, centerStyle);
        }

        private void DrawCharacterSelect()
        {
            float width = Mathf.Min(760f, Screen.width - 30f);
            float left = (Screen.width - width) * 0.5f;
            Rect panel = new Rect(left, Mathf.Max(25f, Screen.height * 0.5f - 210f), width, 420f);
            GUI.DrawTexture(panel, panelTexture);

            GUI.Label(new Rect(left + 20, panel.y + 22, width - 40, 50), "CHOOSE YOUR CHARACTER", centerStyle);
            GUI.Label(new Rect(left + 20, panel.y + 76, width - 40, 30), "Press 1, 2, 3 or 4 to start", selectStyle);

            string choices =
                "1  MARIO\nBalanced speed, jump and throw\n\n" +
                "2  LUIGI\nHigher jump, looser air control\n\n" +
                "3  PEACH\nHold jump while falling to float\n\n" +
                "4  TOAD\nFast movement and strongest throw";

            GUI.Label(new Rect(left + 45, panel.y + 120, width - 90, 270), choices, selectStyle);
        }

        private void OnDestroy()
        {
            if (panelTexture != null)
                Destroy(panelTexture);
        }
    }
}
