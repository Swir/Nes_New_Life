#if UNITY_EDITOR
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace NesNewLife.SMB2.EditorTools
{
    public static class CreateCampaignScenes
    {
        public const string StageDirectory = "Assets/NesNewLife/SMB2/Campaign";
        public const string Stage01Path = StageDirectory + "/SMB2_Stage_01.unity";
        public const string Stage02Path = StageDirectory + "/SMB2_Stage_02.unity";
        public const string Stage03Path = StageDirectory + "/SMB2_Stage_03.unity";

        public static readonly string[] StagePaths = { Stage01Path, Stage02Path, Stage03Path };

        [MenuItem("NES New Life/SMB2/Create 3-Stage Campaign")]
        public static void Create()
        {
            Directory.CreateDirectory(StageDirectory);

            CreatePrototypeScene.CreatePlayable();
            const string sourcePath = "Assets/NesNewLife/SMB2/Prototype/SMB2_Playable.unity";
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            if (!File.Exists(sourcePath))
            {
                Debug.LogError("NES New Life: base playable scene was not generated; campaign creation aborted.");
                return;
            }

            for (int i = 0; i < StagePaths.Length; i++)
            {
                string stagePath = StagePaths[i];
                if (AssetDatabase.LoadAssetAtPath<SceneAsset>(stagePath) != null)
                    AssetDatabase.DeleteAsset(stagePath);

                if (!AssetDatabase.CopyAsset(sourcePath, stagePath))
                {
                    Debug.LogError($"NES New Life: failed to create {stagePath}.");
                    return;
                }

                ConfigureStage(stagePath, i + 1);
            }

            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene(Stage01Path, true),
                new EditorBuildSettingsScene(Stage02Path, true),
                new EditorBuildSettingsScene(Stage03Path, true)
            };

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            EditorSceneManager.OpenScene(Stage01Path);
            Debug.Log("NES New Life: 3-stage campaign generated and registered in Build Settings.");
        }

        private static void ConfigureStage(string path, int stageNumber)
        {
            var scene = EditorSceneManager.OpenScene(path, OpenSceneMode.Single);

            CampaignStageDefinition definition = Object.FindFirstObjectByType<CampaignStageDefinition>();
            if (definition == null)
            {
                GameObject stageObject = new GameObject("Campaign Stage");
                definition = stageObject.AddComponent<CampaignStageDefinition>();
            }

            bool finalStage = stageNumber == CampaignCatalog.StageCount;
            string nextScene = finalStage ? string.Empty : CampaignCatalog.SceneForStage(stageNumber + 1);
            definition.Configure(stageNumber, CampaignCatalog.DisplayNameForStage(stageNumber), nextScene, finalStage, 2000 + stageNumber * 1000);

            ApplyVisualVariant(stageNumber);
            ApplyDifficultyVariant(stageNumber);
            EditorSceneManager.SaveScene(scene, path);
        }

        private static void ApplyVisualVariant(int stageNumber)
        {
            Camera camera = Object.FindFirstObjectByType<Camera>();
            if (camera != null)
            {
                camera.backgroundColor = stageNumber switch
                {
                    1 => new Color(0.035f, 0.075f, 0.12f),
                    2 => new Color(0.07f, 0.045f, 0.11f),
                    _ => new Color(0.12f, 0.035f, 0.045f)
                };
            }

            SpriteRenderer[] renderers = Object.FindObjectsByType<SpriteRenderer>(FindObjectsSortMode.None);
            foreach (SpriteRenderer renderer in renderers)
            {
                if (!renderer.name.Contains("Backdrop"))
                    continue;

                renderer.color = stageNumber switch
                {
                    1 => new Color(0.08f, 0.15f, 0.22f),
                    2 => new Color(0.14f, 0.10f, 0.20f),
                    _ => new Color(0.20f, 0.08f, 0.10f)
                };
            }
        }

        private static void ApplyDifficultyVariant(int stageNumber)
        {
            BossController boss = Object.FindFirstObjectByType<BossController>();
            if (boss != null)
            {
                EnemyHealth health = boss.GetComponent<EnemyHealth>();
                if (health != null)
                    health.Configure(3 + stageNumber * 2, 1500 + stageNumber * 1000);
            }

            EnemyPatroller[] patrollers = Object.FindObjectsByType<EnemyPatroller>(FindObjectsSortMode.None);
            for (int i = 0; i < patrollers.Length; i++)
            {
                Rigidbody2D body = patrollers[i].GetComponent<Rigidbody2D>();
                if (body != null)
                    body.gravityScale = 3f + (stageNumber - 1) * 0.15f;
            }

            if (stageNumber == 1)
                return;

            List<GameObject> platforms = new List<GameObject>();
            foreach (BoxCollider2D collider in Object.FindObjectsByType<BoxCollider2D>(FindObjectsSortMode.None))
            {
                if (collider.gameObject.name == "Platform")
                    platforms.Add(collider.gameObject);
            }

            platforms.Sort((a, b) => a.transform.position.x.CompareTo(b.transform.position.x));
            for (int i = 0; i < platforms.Count; i++)
            {
                Vector3 position = platforms[i].transform.position;
                float wave = (i % 2 == 0 ? 1f : -1f) * (stageNumber - 1) * 0.45f;
                position.y += wave;
                platforms[i].transform.position = position;
            }
        }
    }
}
#endif
