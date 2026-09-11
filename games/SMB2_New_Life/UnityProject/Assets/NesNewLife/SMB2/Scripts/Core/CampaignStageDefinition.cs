using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class CampaignStageDefinition : MonoBehaviour
    {
        [SerializeField, Min(1)] private int stageNumber = 1;
        [SerializeField] private string stageName = "Stage 1";
        [SerializeField] private string nextSceneName = string.Empty;
        [SerializeField] private bool finalStage;
        [SerializeField, Min(0)] private int completionBonus = 2500;

        public int StageNumber => Mathf.Max(1, stageNumber);
        public string StageName => string.IsNullOrWhiteSpace(stageName) ? $"Stage {StageNumber}" : stageName;
        public string NextSceneName => nextSceneName ?? string.Empty;
        public bool FinalStage => finalStage;
        public int CompletionBonus => Mathf.Max(0, completionBonus);

        public void Configure(int number, string displayName, string nextScene, bool isFinal, int bonus)
        {
            stageNumber = Mathf.Max(1, number);
            stageName = string.IsNullOrWhiteSpace(displayName) ? $"Stage {stageNumber}" : displayName;
            nextSceneName = nextScene ?? string.Empty;
            finalStage = isFinal;
            completionBonus = Mathf.Max(0, bonus);
        }
    }
}
