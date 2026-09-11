#if UNITY_EDITOR
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace NesNewLife.SMB2.EditorTools
{
    public static class CreatePrototypeScene
    {
        private const string SceneDirectory = "Assets/NesNewLife/SMB2/Prototype";
        private const string ScenePath = SceneDirectory + "/SMB2_Playable.unity";
        private const int GroundLayer = 8;
        private const int CarryableLayer = 9;

        [MenuItem("NES New Life/SMB2/Create PLAYABLE Level")]
        public static void CreatePlayable()
        {
            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            Sprite sprite = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd");

            CreateManagers();
            CreateBackdrop(sprite);

            CreateGround(-18f, 10f, sprite);
            CreateGround(-5f, 12f, sprite);
            CreateGround(10f, 14f, sprite);
            CreateGround(28f, 16f, sprite);
            CreateGround(48f, 20f, sprite);

            CreatePlatform(new Vector2(-12f, -0.2f), new Vector2(4f, 0.55f), sprite);
            CreatePlatform(new Vector2(-2f, 1.0f), new Vector2(4f, 0.55f), sprite);
            CreatePlatform(new Vector2(8f, 2.0f), new Vector2(5f, 0.55f), sprite);
            CreatePlatform(new Vector2(21f, 0.4f), new Vector2(5f, 0.55f), sprite);
            CreatePlatform(new Vector2(34f, 1.8f), new Vector2(5f, 0.55f), sprite);
            CreatePlatform(new Vector2(45f, 3.0f), new Vector2(5f, 0.55f), sprite);

            GameObject player = CreatePlayer(new Vector2(-21f, -1.15f), sprite);

            CreateCarryable(new Vector2(-16.5f, -1.55f), sprite, new Color(0.98f, 0.54f, 0.18f));
            CreateCarryable(new Vector2(-8f, -1.55f), sprite, new Color(0.95f, 0.31f, 0.24f));
            CreateCarryable(new Vector2(3f, -1.55f), sprite, new Color(0.85f, 0.40f, 0.92f));
            CreateCarryable(new Vector2(24f, -1.55f), sprite, new Color(0.98f, 0.70f, 0.20f));
            CreateCarryable(new Vector2(39.5f, -1.55f), sprite, new Color(0.34f, 0.82f, 0.64f));
            CreateCarryable(new Vector2(43f, -1.55f), sprite, new Color(0.95f, 0.56f, 0.18f));
            CreateCarryable(new Vector2(50f, -1.55f), sprite, new Color(0.42f, 0.76f, 1f));

            CreateEnemy(new Vector2(-11.5f, 0.55f), -13.5f, -10.5f, 1.6f, sprite);
            CreateEnemy(new Vector2(1f, -1.35f), -1f, 4f, 2.0f, sprite);
            CreateEnemy(new Vector2(9f, 2.7f), 6.2f, 10.2f, 1.9f, sprite);
            CreateEnemy(new Vector2(18f, -1.35f), 15f, 22f, 2.3f, sprite);
            CreateEnemy(new Vector2(34f, 2.5f), 31.8f, 36.2f, 2.1f, sprite);
            CreateBoss(new Vector2(47f, -1.0f), 41f, 51f, sprite);

            CreateScorePickup(new Vector2(-12f, 1.0f), sprite);
            CreateScorePickup(new Vector2(-2f, 2.0f), sprite);
            CreateScorePickup(new Vector2(8f, 3.0f), sprite);
            CreateScorePickup(new Vector2(21f, 1.4f), sprite);
            CreateScorePickup(new Vector2(34f, 2.8f), sprite);
            CreateScorePickup(new Vector2(45f, 4.0f), sprite);

            CreateHeart(new Vector2(6f, -1.3f), sprite);
            CreateHeart(new Vector2(31f, -1.3f), sprite);
            CreateCheckpoint(new Vector2(25f, -1.15f), sprite);
            CreateExit(new Vector2(56f, -0.55f), sprite);
            CreateKillZone(new Vector2(15f, -7.5f), new Vector2(105f, 4f));
            CreateCamera(player.transform);

            Directory.CreateDirectory(SceneDirectory);
            AssetDatabase.Refresh();
            EditorSceneManager.SaveScene(scene, ScenePath);
            EnsureSceneInBuildSettings();

            Selection.activeGameObject = player;
            EditorGUIUtility.PingObject(player);
            Debug.Log("NES New Life: PLAYABLE SMB2 vertical slice created. Press Play. Controls: A/D, Space, Shift, 1-4.");
        }

        [MenuItem("NES New Life/SMB2/Create Prototype Scene")]
        public static void CreateLegacyMenuAlias() => CreatePlayable();

        private static void CreateManagers()
        {
            GameObject manager = new GameObject("GameManager");
            manager.AddComponent<GameManager>();
            GameObject hud = new GameObject("HUD");
            hud.AddComponent<GameHud>();
        }

        private static GameObject CreatePlayer(Vector2 position, Sprite sprite)
        {
            GameObject player = CreateBlock("Player", position, new Vector2(0.85f, 1.45f), CharacterTuning.For(CharacterType.Mario).Color, sprite);
            Rigidbody2D body = player.AddComponent<Rigidbody2D>();
            body.gravityScale = 3f;
            body.freezeRotation = true;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;
            BoxCollider2D collider = player.AddComponent<BoxCollider2D>();
            collider.size = new Vector2(0.9f, 1f);

            GameObject groundCheck = new GameObject("GroundCheck");
            groundCheck.transform.SetParent(player.transform);
            groundCheck.transform.localPosition = new Vector3(0f, -0.58f, 0f);
            GameObject pickupPoint = new GameObject("PickupPoint");
            pickupPoint.transform.SetParent(player.transform);
            pickupPoint.transform.localPosition = new Vector3(0f, -0.35f, 0f);
            GameObject carryAnchor = new GameObject("CarryAnchor");
            carryAnchor.transform.SetParent(player.transform);
            carryAnchor.transform.localPosition = new Vector3(0f, 0.95f, 0f);

            PlayerController2D controller = player.AddComponent<PlayerController2D>();
            SerializedObject controllerSO = new SerializedObject(controller);
            controllerSO.FindProperty("groundCheck").objectReferenceValue = groundCheck.transform;
            controllerSO.FindProperty("groundMask").intValue = 1 << GroundLayer;
            controllerSO.ApplyModifiedPropertiesWithoutUndo();

            CarrySystem2D carry = player.AddComponent<CarrySystem2D>();
            SerializedObject carrySO = new SerializedObject(carry);
            carrySO.FindProperty("pickupPoint").objectReferenceValue = pickupPoint.transform;
            carrySO.FindProperty("carryAnchor").objectReferenceValue = carryAnchor.transform;
            carrySO.FindProperty("carryableMask").intValue = 1 << CarryableLayer;
            carrySO.ApplyModifiedPropertiesWithoutUndo();
            player.AddComponent<PlayerHealth>();
            return player;
        }

        private static void CreateEnemy(Vector2 position, float left, float right, float speed, Sprite sprite)
        {
            GameObject enemy = CreateBlock("Enemy_Patroller", position, new Vector2(0.9f, 0.9f), new Color(0.75f, 0.28f, 0.25f), sprite);
            Rigidbody2D body = enemy.AddComponent<Rigidbody2D>();
            body.gravityScale = 3f;
            body.freezeRotation = true;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            enemy.AddComponent<BoxCollider2D>();
            enemy.AddComponent<EnemyHealth>();
            enemy.AddComponent<DamageOnContact>();
            EnemyPatroller patrol = enemy.AddComponent<EnemyPatroller>();
            patrol.Configure(left, right, speed);
        }

        private static void CreateBoss(Vector2 position, float left, float right, Sprite sprite)
        {
            GameObject boss = CreateBlock("MINIBOSS", position, new Vector2(1.7f, 1.7f), new Color(0.72f, 0.20f, 0.85f), sprite);
            Rigidbody2D body = boss.AddComponent<Rigidbody2D>();
            body.gravityScale = 3.2f;
            body.freezeRotation = true;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            boss.AddComponent<BoxCollider2D>();
            EnemyHealth health = boss.AddComponent<EnemyHealth>();
            health.Configure(5, 2500);
            boss.AddComponent<DamageOnContact>();
            BossController controller = boss.AddComponent<BossController>();
            controller.Configure(left, right);
        }

        private static void CreateCarryable(Vector2 position, Sprite sprite, Color color)
        {
            GameObject obj = CreateBlock("Carryable", position, new Vector2(0.55f, 0.55f), color, sprite);
            obj.layer = CarryableLayer;
            Rigidbody2D body = obj.AddComponent<Rigidbody2D>();
            body.gravityScale = 2.5f;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            obj.AddComponent<BoxCollider2D>();
            obj.AddComponent<CarryableObject2D>();
        }

        private static void CreateScorePickup(Vector2 position, Sprite sprite)
        {
            GameObject pickup = CreateBlock("ScorePickup", position, new Vector2(0.35f, 0.35f), new Color(1f, 0.88f, 0.22f), sprite);
            CircleCollider2D collider = pickup.AddComponent<CircleCollider2D>();
            collider.isTrigger = true;
            pickup.AddComponent<ScorePickup>();
        }

        private static void CreateHeart(Vector2 position, Sprite sprite)
        {
            GameObject heart = CreateBlock("Heart", position, new Vector2(0.48f, 0.48f), new Color(1f, 0.18f, 0.38f), sprite);
            CircleCollider2D collider = heart.AddComponent<CircleCollider2D>();
            collider.isTrigger = true;
            heart.AddComponent<HeartPickup>();
        }

        private static void CreateCheckpoint(Vector2 position, Sprite sprite)
        {
            GameObject checkpoint = CreateBlock("Checkpoint", position, new Vector2(0.35f, 2.6f), new Color(0.30f, 0.58f, 1f), sprite);
            BoxCollider2D collider = checkpoint.AddComponent<BoxCollider2D>();
            collider.isTrigger = true;
            checkpoint.AddComponent<CheckpointTrigger>();
        }

        private static void CreateExit(Vector2 position, Sprite sprite)
        {
            GameObject exit = CreateBlock("LEVEL EXIT", position, new Vector2(1.6f, 3.4f), new Color(0.30f, 0.95f, 0.70f), sprite);
            BoxCollider2D collider = exit.AddComponent<BoxCollider2D>();
            collider.isTrigger = true;
            exit.AddComponent<LevelExit>();
        }

        private static void CreateKillZone(Vector2 position, Vector2 size)
        {
            GameObject zone = new GameObject("Fall Kill Zone");
            zone.transform.position = position;
            BoxCollider2D collider = zone.AddComponent<BoxCollider2D>();
            collider.size = size;
            collider.isTrigger = true;
            zone.AddComponent<KillZone>();
        }

        private static void CreateGround(float centerX, float width, Sprite sprite)
        {
            GameObject ground = CreateBlock("Ground", new Vector2(centerX, -2.5f), new Vector2(width, 1f), new Color(0.15f, 0.22f, 0.30f), sprite);
            ground.layer = GroundLayer;
            ground.AddComponent<BoxCollider2D>();
        }

        private static void CreatePlatform(Vector2 position, Vector2 scale, Sprite sprite)
        {
            GameObject platform = CreateBlock("Platform", position, scale, new Color(0.30f, 0.44f, 0.52f), sprite);
            platform.layer = GroundLayer;
            platform.AddComponent<BoxCollider2D>();
        }

        private static GameObject CreateBlock(string name, Vector2 position, Vector2 scale, Color color, Sprite sprite)
        {
            GameObject obj = new GameObject(name);
            obj.transform.position = position;
            obj.transform.localScale = new Vector3(scale.x, scale.y, 1f);
            SpriteRenderer renderer = obj.AddComponent<SpriteRenderer>();
            renderer.sprite = sprite;
            renderer.color = color;
            return obj;
        }

        private static void CreateBackdrop(Sprite sprite)
        {
            for (int i = 0; i < 9; i++)
            {
                float x = -22f + i * 10f;
                GameObject hill = CreateBlock("Backdrop", new Vector2(x, -0.2f), new Vector2(8f, 7f), new Color(0.08f + i * 0.006f, 0.12f, 0.20f), sprite);
                hill.GetComponent<SpriteRenderer>().sortingOrder = -20;
            }
        }

        private static void CreateCamera(Transform target)
        {
            GameObject cameraObject = new GameObject("Main Camera");
            cameraObject.tag = "MainCamera";
            cameraObject.transform.position = new Vector3(target.position.x, 0.5f, -10f);
            Camera camera = cameraObject.AddComponent<Camera>();
            camera.orthographic = true;
            camera.orthographicSize = 5.3f;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.035f, 0.055f, 0.10f);
            CameraFollow2D follow = cameraObject.AddComponent<CameraFollow2D>();
            follow.Target = target;
        }

        private static void EnsureSceneInBuildSettings()
        {
            List<EditorBuildSettingsScene> scenes = new List<EditorBuildSettingsScene>(EditorBuildSettings.scenes);
            if (!scenes.Exists(s => s.path == ScenePath))
            {
                scenes.Add(new EditorBuildSettingsScene(ScenePath, true));
                EditorBuildSettings.scenes = scenes.ToArray();
            }
        }
    }
}
#endif
