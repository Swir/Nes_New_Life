using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class GameHud : MonoBehaviour
    {
        private GUIStyle titleStyle;
        private GUIStyle textStyle;
        private GUIStyle centerStyle;
        private Texture2D panelTexture;

        private void Awake()
        {
            panelTexture = new Texture2D(1, 1);
            panelTexture.SetPixel(0, 0, new Color(0.03f, 0.05f, 0.08f, 0.88f));
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
        }

        private void OnGUI()
        {
            EnsureStyles();
            GameManager gm = GameManager.Instance;
            if (gm == null)
                return;

            PlayerHealth health = FindFirstObjectByType<PlayerHealth>();
            CharacterTuning tuning = CharacterTuning.For(gm.SelectedCharacter);

            Rect panel = new Rect(18, 18, 355, 142);
            GUI.DrawTexture(panel, panelTexture);
            GUI.Label(new Rect(34, 28, 320, 30), "NES NEW LIFE #001", titleStyle);
            GUI.Label(new Rect(34, 62, 320, 26), $"{tuning.DisplayName}   HP: {(health != null ? health.CurrentHealth : 0)}/{(health != null ? health.MaxHealth : 0)}", textStyle);
            GUI.Label(new Rect(34, 88, 320, 26), $"Lives: {gm.Lives}   Score: {gm.Score:000000}", textStyle);
            GUI.Label(new Rect(34, 116, 320, 30), "Move A/D • Jump Space • Carry/Throw Shift", textStyle);

            Rect hint = new Rect(Screen.width - 305, 18, 285, 110);
            GUI.DrawTexture(hint, panelTexture);
            GUI.Label(new Rect(hint.x + 14, hint.y + 10, 260, 26), "Character hotkeys", titleStyle);
            GUI.Label(new Rect(hint.x + 14, hint.y + 43, 260, 50), "1 Mario  •  2 Luigi\n3 Peach  •  4 Toad", textStyle);

            if (gm.State == RunState.Playing)
                return;

            Rect overlay = new Rect(Screen.width * 0.5f - 260, Screen.height * 0.5f - 100, 520, 200);
            GUI.DrawTexture(overlay, panelTexture);
            string message = gm.State == RunState.Won
                ? $"LEVEL COMPLETE!\nScore: {gm.Score:000000}\n\nPress R to replay"
                : "GAME OVER\n\nPress R to restart";
            GUI.Label(overlay, message, centerStyle);
        }

        private void OnDestroy()
        {
            if (panelTexture != null)
                Destroy(panelTexture);
        }
    }
}
