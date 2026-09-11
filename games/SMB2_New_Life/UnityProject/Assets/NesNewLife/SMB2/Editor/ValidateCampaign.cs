#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace NesNewLife.SMB2.EditorTools
{
    public static class ValidateCampaign
    {
        [MenuItem("NES New Life/SMB2/Validate 3-Stage Campaign")]
        public static void Validate()
        {
            int errors = 0;
            int warnings = 0;

            for (int i = 0; i < CreateCampaignScenes.StagePaths.Length; i++)
            {
                string path = CreateCampaignScenes.StagePaths[i];
                int expectedStage = i + 1;

                if (!File.Exists(path))
                {
                    Debug.LogError($"Campaign validation: missing scene {path}");
                    errors++;
                    continue;
                }

                EditorSceneManager.OpenScene(path, OpenSceneMode.Single);
                CampaignStageDefinition stage = Object.FindFirstObjectByType<CampaignStageDefinition>();
                if (stage == null)
                {
                    Debug.LogError($"Campaign validation: Stage {expectedStage} has no CampaignStageDefinition.");
                    errors++;
                }
                else
                {
                    if (stage.StageNumber != expectedStage)
                    {
                        Debug.LogError($"Campaign validation: {path} reports Stage {stage.StageNumber}, expected {expectedStage}.");
                        errors++;
                    }

                    bool shouldBeFinal = expectedStage == CampaignCatalog.StageCount;
                    if (stage.FinalStage != shouldBeFinal)
                    {
                        Debug.LogError($"Campaign validation: Stage {expectedStage} final-stage flag is incorrect.");
                        errors++;
                    }
                }

                if (Object.FindFirstObjectByType<GameManager>() == null) { Debug.LogError($"Stage {expectedStage}: missing GameManager."); errors++; }
                if (Object.FindFirstObjectByType<PlayerController2D>() == null) { Debug.LogError($"Stage {expectedStage}: missing player."); errors++; }
                if (Object.FindFirstObjectByType<LevelExit>() == null) { Debug.LogError($"Stage {expectedStage}: missing LevelExit."); errors++; }
                if (Object.FindFirstObjectByType<BossController>() == null) { Debug.LogWarning($"Stage {expectedStage}: no boss/guardian found."); warnings++; }
                if (Object.FindFirstObjectByType<CameraFollow2D>() == null) { Debug.LogWarning($"Stage {expectedStage}: no CameraFollow2D found."); warnings++; }
            }

            if (File.Exists(CreateCampaignScenes.Stage01Path))
                EditorSceneManager.OpenScene(CreateCampaignScenes.Stage01Path, OpenSceneMode.Single);

            string summary = $"Campaign validation complete: {errors} error(s), {warnings} warning(s).";
            if (errors == 0)
                Debug.Log(summary);
            else
                Debug.LogError(summary);

            EditorUtility.DisplayDialog("NES New Life — Campaign Validation", summary, "OK");
        }
    }
}
#endif
