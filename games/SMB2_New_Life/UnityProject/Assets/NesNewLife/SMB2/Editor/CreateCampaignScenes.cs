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
            ApplyTraversalAndHazardVariant(stageNumber);
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

        private static void ApplyTraversalAndHazardVariant(int stageNumber)
        {
            Sprite prototypeSprite = FindPrototypeSprite();
            if (prototypeSprite == null)
            {
                Debug.LogWarning($"NES New Life: Stage {stageNumber} traversal pass skipped because no prototype sprite was found.");
                return;
            }

            if (stageNumber == 1)
            {
                CreateClimbable(new Vector2(20.5f, 1.6f), new Vector2(0.7f, 4.8f), prototypeSprite);
                CreateGroundLedge(new Vector2(20.5f, 4.1f), new Vector2(3.2f, 0.45f), prototypeSprite);
                return;
            }

            LevelExit exit = Object.FindFirstObjectByType<LevelExit>();
            if (exit != null)
                exit.transform.position = new Vector3(53f, 5.7f, exit.transform.position.z);

            CreateClimbable(new Vector2(52.6f, 1.5f), new Vector2(0.8f, 7.6f), prototypeSprite);
            CreateGroundLedge(new Vector2(52.6f, 4.65f), new Vector2(4.4f, 0.5f), prototypeSprite);
            CreateMovingPlatform(new Vector2(37.5f, -0.7f), new Vector2(2.7f, 0.45f), new Vector2(0f, 4.2f), 1.7f + stageNumber * 0.25f, prototypeSprite);
            CreateCrumblePlatform(new Vector2(42.2f, 1.25f), new Vector2(2.4f, 0.42f), prototypeSprite);
            CreateSpikes(new Vector2(46.2f, -1.72f), new Vector2(1.8f, 0.35f), prototypeSprite);
            CreateSpikes(new Vector2(49.2f, -1.72f), new Vector2(1.5f, 0.35f), prototypeSprite);

            if (stageNumber >= 3)
            {
                CreateMovingPlatform(new Vector2(45.0f, 1.2f), new Vector2(2.4f, 0.42f), new Vector2(3.6f, 0f), 2.5f, prototypeSprite);
                ReplaceGuardianWithChargeBoss();
            }
        }

        private static Sprite FindPrototypeSprite()
        {
            PlayerController2D player = Object.FindFirstObjectByType<PlayerController2D>();
            if (player != null)
            {
                SpriteRenderer renderer = player.GetComponent<SpriteRenderer>();
                if (renderer != null && renderer.sprite != null)
                    return renderer.sprite;
            }

            foreach (SpriteRenderer renderer in Object.FindObjectsByType<SpriteRenderer>(FindObjectsSortMode.None))
            {
                if (renderer.sprite != null)
                    return renderer.sprite;
            }

            return null;
        }

        private static void CreateClimbable(Vector2 position, Vector2 size, Sprite sprite)
        {
            GameObject vine = CreateBlock("Climbable Vine", position, size, new Color(0.22f, 0.72f, 0.38f, 0.72f), sprite);
            SpriteRenderer renderer = vine.GetComponent<SpriteRenderer>();
            renderer.sortingOrder = -1;
            BoxCollider2D collider = vine.AddComponent<BoxCollider2D>();
            collider.isTrigger = true;
            vine.AddComponent<ClimbableZone2D>();
        }

        private static void CreateGroundLedge(Vector2 position, Vector2 size, Sprite sprite)
        {
            GameObject ledge = CreateBlock("Vertical Ledge", position, size, new Color(0.31f, 0.45f, 0.54f), sprite);
            ledge.layer = 8;
            ledge.AddComponent<BoxCollider2D>();
        }

        private static void CreateMovingPlatform(Vector2 position, Vector2 size, Vector2 travel, float speed, Sprite sprite)
        {
            GameObject platform = CreateBlock("Moving Platform", position, size, new Color(0.34f, 0.70f, 0.92f), sprite);
            platform.layer = 8;
            Rigidbody2D body = platform.AddComponent<Rigidbody2D>();
            body.bodyType = RigidbodyType2D.Kinematic;
            body.freezeRotation = true;
            platform.AddComponent<BoxCollider2D>();
            MovingPlatform2D mover = platform.AddComponent<MovingPlatform2D>();
            mover.Configure(travel, speed);
        }

        private static void CreateCrumblePlatform(Vector2 position, Vector2 size, Sprite sprite)
        {
            GameObject platform = CreateBlock("Crumble Platform", position, size, new Color(0.88f, 0.56f, 0.25f), sprite);
            platform.layer = 8;
            platform.AddComponent<BoxCollider2D>();
            platform.AddComponent<CrumblePlatform2D>();
        }

        private static void CreateSpikes(Vector2 position, Vector2 size, Sprite sprite)
        {
            GameObject spikes = CreateBlock("Spike Hazard", position, size, new Color(0.95f, 0.22f, 0.30f), sprite);
            BoxCollider2D collider = spikes.AddComponent<BoxCollider2D>();
            collider.isTrigger = true;
            spikes.AddComponent<SpikeHazard2D>();
        }

        private static void ReplaceGuardianWithChargeBoss()
        {
            BossController oldBoss = Object.FindFirstObjectByType<BossController>();
            if (oldBoss == null)
                return;

            GameObject bossObject = oldBoss.gameObject;
            Object.DestroyImmediate(oldBoss);
            ChargeBossController chargeBoss = bossObject.AddComponent<ChargeBossController>();
            chargeBoss.Configure(42f, 50f, 1.12f);

            SpriteRenderer renderer = bossObject.GetComponent<SpriteRenderer>();
            if (renderer != null)
                renderer.color = new Color(0.92f, 0.23f, 0.60f);

            EnemyHealth health = bossObject.GetComponent<EnemyHealth>();
            if (health != null)
                health.Configure(9, 5000);

            bossObject.name = "Charge Guardian";
        }

        private static GameObject CreateBlock(string name, Vector2 position, Vector2 size, Color color, Sprite sprite)
        {
            GameObject obj = new GameObject(name);
            obj.transform.position = position;
            obj.transform.localScale = new Vector3(size.x, size.y, 1f);
            SpriteRenderer renderer = obj.AddComponent<SpriteRenderer>();
            renderer.sprite = sprite;
            renderer.color = color;
            return obj;
        }
    }
}
#endif
