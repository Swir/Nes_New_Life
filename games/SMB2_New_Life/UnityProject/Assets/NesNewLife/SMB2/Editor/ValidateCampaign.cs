#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace NesNewLife.SMB2.EditorTools
{
    public static class ValidateCampaign
    {
        [MenuItem("NES New Life/SMB2/Validate 20-Stage Campaign")]
        public static void Validate()
        {
            int errors = 0;
            int warnings = 0;
            int checkedStages = 0;

            if (CreateCampaignScenes.StagePaths.Length != CampaignCatalog.StageCount)
            {
                Debug.LogError($"Campaign validation: generator exposes {CreateCampaignScenes.StagePaths.Length} paths, catalog expects {CampaignCatalog.StageCount}.");
                errors++;
            }

            for (int i = 0; i < CreateCampaignScenes.StagePaths.Length; i++)
            {
                string path = CreateCampaignScenes.StagePaths[i];
                int expectedStage = i + 1;
                int world = CampaignCatalog.WorldForStage(expectedStage);
                int level = CampaignCatalog.LevelForStage(expectedStage);

                if (!File.Exists(path))
                {
                    Debug.LogError($"Campaign validation: missing scene {path}");
                    errors++;
                    continue;
                }

                checkedStages++;
                EditorSceneManager.OpenScene(path, OpenSceneMode.Single);
                CampaignStageDefinition stage = Object.FindFirstObjectByType<CampaignStageDefinition>();
                if (stage == null)
                {
                    Debug.LogError($"Campaign validation: {world}-{level} has no CampaignStageDefinition.");
                    errors++;
                }
                else
                {
                    if (stage.StageNumber != expectedStage)
                    {
                        Debug.LogError($"Campaign validation: {path} reports Stage {stage.StageNumber}, expected {expectedStage}.");
                        errors++;
                    }

                    if (stage.StageName != CampaignCatalog.DisplayNameForStage(expectedStage))
                    {
                        Debug.LogWarning($"Campaign validation: Stage {expectedStage} display name differs from catalog.");
                        warnings++;
                    }

                    bool shouldBeFinal = expectedStage == CampaignCatalog.StageCount;
                    if (stage.FinalStage != shouldBeFinal)
                    {
                        Debug.LogError($"Campaign validation: Stage {expectedStage} final-stage flag is incorrect.");
                        errors++;
                    }
                }

                if (Object.FindFirstObjectByType<GameManager>() == null) { Debug.LogError($"{world}-{level}: missing GameManager."); errors++; }
                if (Object.FindFirstObjectByType<PlayerController2D>() == null) { Debug.LogError($"{world}-{level}: missing player."); errors++; }
                if (Object.FindFirstObjectByType<LevelExit>() == null) { Debug.LogError($"{world}-{level}: missing LevelExit."); errors++; }
                if (Object.FindFirstObjectByType<CameraFollow2D>() == null) { Debug.LogWarning($"{world}-{level}: no CameraFollow2D found."); warnings++; }
                if (Object.FindFirstObjectByType<ClimbableZone2D>() == null) { Debug.LogError($"{world}-{level}: missing climbable traversal zone."); errors++; }

                bool hasGuardian = Object.FindFirstObjectByType<BossController>() != null || Object.FindFirstObjectByType<ChargeBossController>() != null;
                if (!hasGuardian) { Debug.LogError($"{world}-{level}: no guardian archetype found."); errors++; }

                if (world >= 2 || level >= 2)
                {
                    if (Object.FindFirstObjectByType<MovingPlatform2D>() == null)
                    {
                        Debug.LogError($"{world}-{level}: expected moving platform was not generated.");
                        errors++;
                    }
                }

                if (world >= 3 || level == 3)
                {
                    if (Object.FindFirstObjectByType<CrumblePlatform2D>() == null)
                    {
                        Debug.LogError($"{world}-{level}: expected crumble platform was not generated.");
                        errors++;
                    }
                }

                if (world >= 2)
                {
                    if (Object.FindFirstObjectByType<SpikeHazard2D>() == null)
                    {
                        Debug.LogError($"{world}-{level}: expected spike hazard was not generated.");
                        errors++;
                    }
                }

                if (CampaignCatalog.IsWorldFinale(expectedStage) && world >= 3 && Object.FindFirstObjectByType<ChargeBossController>() == null)
                {
                    Debug.LogError($"{world}-{level}: world finale should contain a charge guardian.");
                    errors++;
                }
            }

            if (CreateCampaignScenes.StagePaths.Length > 0 && File.Exists(CreateCampaignScenes.StagePaths[0]))
                EditorSceneManager.OpenScene(CreateCampaignScenes.StagePaths[0], OpenSceneMode.Single);

            string summary = $"Campaign validation complete: {checkedStages}/{CampaignCatalog.StageCount} stage(s) checked, {errors} error(s), {warnings} warning(s).";
            if (errors == 0) Debug.Log(summary); else Debug.LogError(summary);
            EditorUtility.DisplayDialog("NES New Life — Campaign Validation", summary, "OK");
        }
    }
}
#endif
