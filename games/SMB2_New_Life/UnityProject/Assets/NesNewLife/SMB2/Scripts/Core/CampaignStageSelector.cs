using UnityEngine;
using UnityEngine.SceneManagement;

namespace NesNewLife.SMB2
{
    public sealed class CampaignStageSelector : MonoBehaviour
    {
        private int selectedStage = 1;

        public int SelectedStage => selectedStage;
        public string SelectedStageName => CampaignCatalog.DisplayNameForStage(selectedStage);
        public int HighestUnlockedStage => Mathf.Clamp(CampaignSave.HighestUnlockedStage, 1, CampaignCatalog.StageCount);

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            GameManager gm = Object.FindFirstObjectByType<GameManager>();
            if (gm != null && gm.GetComponent<CampaignStageSelector>() == null)
                gm.gameObject.AddComponent<CampaignStageSelector>();
        }

        private void OnEnable()
        {
            selectedStage = Mathf.Clamp(
                CampaignSave.CampaignActive ? CampaignSave.CurrentStage : CampaignSave.HighestUnlockedStage,
                1,
                HighestUnlockedStage);
        }

        private void Update()
        {
            GameManager gm = GameManager.Instance;
            if (gm == null || gm.State != RunState.CharacterSelect || !CampaignSave.HasSave)
                return;

            bool changed = false;
            if (Input.GetKeyDown(KeyCode.Q) || Input.GetKeyDown(KeyCode.LeftBracket))
            {
                selectedStage--;
                changed = true;
            }
            else if (Input.GetKeyDown(KeyCode.E) || Input.GetKeyDown(KeyCode.RightBracket))
            {
                selectedStage++;
                changed = true;
            }

            if (changed)
            {
                selectedStage = Mathf.Clamp(selectedStage, 1, HighestUnlockedStage);
                gm.ShowMessage($"Stage select: {CampaignCatalog.DisplayNameForStage(selectedStage)}", 1.2f);
            }

            if (!Input.GetKeyDown(KeyCode.Return) && !Input.GetKeyDown(KeyCode.KeypadEnter))
                return;

            CharacterType character = CampaignSave.LastCharacter;
            CampaignSave.BeginCampaign(character, selectedStage, 3, 0);
            CampaignRuntimeBridge.ResumeAfterSceneTransition = true;
            Time.timeScale = 1f;
            SceneManager.LoadScene(CampaignCatalog.SceneForStage(selectedStage));
        }
    }
}
