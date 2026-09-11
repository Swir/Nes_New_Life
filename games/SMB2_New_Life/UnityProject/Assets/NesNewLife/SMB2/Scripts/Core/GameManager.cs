using UnityEngine;
using UnityEngine.SceneManagement;

namespace NesNewLife.SMB2
{
    public enum RunState
    {
        CharacterSelect,
        Playing,
        Paused,
        Settings,
        Won,
        GameOver
    }

    public sealed class GameManager : MonoBehaviour
    {
        public static GameManager Instance { get; private set; }

        [SerializeField] private int startingLives = 3;
        [SerializeField] private CharacterType selectedCharacter = CharacterType.Mario;

        private Transform player;
        private Vector3 checkpoint;
        private int lives;
        private int score;
        private RunState state;
        private RunState stateBeforeSettings;
        private string notificationText = string.Empty;
        private float notificationUntil;
        private CampaignStageDefinition stageDefinition;
        private int stageNumber = 1;
        private string stageName = "Development Stage";

        public int Lives => lives;
        public int Score => score;
        public RunState State => state;
        public CharacterType SelectedCharacter => selectedCharacter;
        public Vector3 Checkpoint => checkpoint;
        public Transform PlayerTransform => player;
        public string NotificationText => Time.unscaledTime <= notificationUntil ? notificationText : string.Empty;
        public bool HasNotification => !string.IsNullOrEmpty(NotificationText);
        public int BestScore => CampaignSave.BestScore;
        public int Clears => CampaignSave.Clears;
        public int TotalDeaths => CampaignSave.Deaths;
        public bool HasSave => CampaignSave.HasSave;
        public int StageNumber => stageNumber;
        public string StageName => stageName;
        public int HighestUnlockedStage => CampaignSave.HighestUnlockedStage;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }

            Instance = this;
            GameSettings.ApplyRuntime();
            stageDefinition = FindFirstObjectByType<CampaignStageDefinition>();
            if (stageDefinition != null)
            {
                stageNumber = stageDefinition.StageNumber;
                stageName = stageDefinition.StageName;
            }

            bool resumeTransition = CampaignRuntimeBridge.ResumeAfterSceneTransition
                && CampaignSave.CampaignActive
                && CampaignSave.CurrentStage == stageNumber;

            CampaignRuntimeBridge.ResumeAfterSceneTransition = false;
            selectedCharacter = CampaignSave.HasSave ? CampaignSave.LastCharacter : selectedCharacter;
            int configuredLives = GameSettings.StartingLives(startingLives);
            lives = resumeTransition ? Mathf.Max(1, CampaignSave.RunLives) : Mathf.Max(1, configuredLives);
            score = resumeTransition ? CampaignSave.RunScore : 0;
            state = resumeTransition ? RunState.Playing : RunState.CharacterSelect;
            Time.timeScale = resumeTransition ? 1f : 0f;

            if (GetComponent<LevelRuntimeEnhancer>() == null)
                gameObject.AddComponent<LevelRuntimeEnhancer>();
        }

        private void Start()
        {
            PlayerController2D controller = FindFirstObjectByType<PlayerController2D>();
            if (controller != null)
            {
                player = controller.transform;
                checkpoint = player.position;
                ApplyCharacter(selectedCharacter);

                if (CampaignSave.CampaignActive && CampaignSave.TryGetCheckpoint(stageNumber, out Vector3 savedCheckpoint))
                {
                    checkpoint = savedCheckpoint;
                    player.position = savedCheckpoint;
                    Rigidbody2D body = player.GetComponent<Rigidbody2D>();
                    if (body != null)
                        body.linearVelocity = Vector2.zero;
                }
            }

            if (state == RunState.Playing)
                ShowMessage($"{stageName} — campaign continues", 2f);
        }

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.F10))
            {
                ToggleSettings();
                return;
            }

            if (state == RunState.Settings)
                return;

            if (state == RunState.CharacterSelect)
            {
                if (CampaignSave.CampaignActive && Input.GetKeyDown(KeyCode.C))
                {
                    ContinueCampaign();
                    return;
                }

                if (Input.GetKeyDown(KeyCode.N))
                {
                    CampaignSave.ResetProgress();
                    selectedCharacter = CharacterType.Mario;
                    ShowMessage("Progress reset — choose 1, 2, 3 or 4", 2f);
                    return;
                }

                if (Input.GetKeyDown(KeyCode.Alpha1)) StartWithCharacter(CharacterType.Mario);
                else if (Input.GetKeyDown(KeyCode.Alpha2)) StartWithCharacter(CharacterType.Luigi);
                else if (Input.GetKeyDown(KeyCode.Alpha3)) StartWithCharacter(CharacterType.Peach);
                else if (Input.GetKeyDown(KeyCode.Alpha4)) StartWithCharacter(CharacterType.Toad);
                return;
            }

            if (state == RunState.Playing && (Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.P)))
            {
                state = RunState.Paused;
                Time.timeScale = 0f;
                return;
            }

            if (state == RunState.Paused && (Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.P)))
            {
                state = RunState.Playing;
                Time.timeScale = 1f;
                return;
            }

            if ((state == RunState.Won || state == RunState.GameOver) && Input.GetKeyDown(KeyCode.R))
            {
                CampaignSave.AbandonCampaign();
                LoadStage(1, false);
            }
        }

        public void ToggleSettings()
        {
            if (state == RunState.Settings)
            {
                state = stateBeforeSettings;
                Time.timeScale = state == RunState.Playing ? 1f : 0f;
                return;
            }

            stateBeforeSettings = state;
            state = RunState.Settings;
            Time.timeScale = 0f;
        }

        public void RegisterPlayer(Transform playerTransform)
        {
            player = playerTransform;
            checkpoint = player.position;
            ApplyCharacter(selectedCharacter);
        }

        public void StartWithCharacter(CharacterType type)
        {
            ApplyCharacter(type);
            lives = Mathf.Max(1, GameSettings.StartingLives(startingLives));
            score = 0;
            CampaignSave.BeginCampaign(type, stageNumber, lives, score);
            checkpoint = player != null ? player.position : checkpoint;
            state = RunState.Playing;
            Time.timeScale = 1f;
            string difficulty = CampaignSave.Clears > 0 ? $"Veteran campaign {CampaignSave.Clears + 1}" : "New campaign";
            ShowMessage($"{difficulty} — {stageName}", 2.6f);
        }

        public void ContinueCampaign()
        {
            if (!CampaignSave.CampaignActive)
            {
                ShowMessage("No active campaign", 1.5f);
                return;
            }

            int savedStage = Mathf.Clamp(CampaignSave.CurrentStage, 1, CampaignCatalog.StageCount);
            selectedCharacter = CampaignSave.LastCharacter;
            lives = Mathf.Max(1, CampaignSave.RunLives);
            score = CampaignSave.RunScore;

            if (savedStage != stageNumber)
            {
                CampaignRuntimeBridge.ResumeAfterSceneTransition = true;
                SceneManager.LoadScene(CampaignCatalog.SceneForStage(savedStage));
                return;
            }

            ApplyCharacter(selectedCharacter);
            if (CampaignSave.TryGetCheckpoint(stageNumber, out Vector3 savedCheckpoint))
            {
                checkpoint = savedCheckpoint;
                if (player != null)
                    player.position = savedCheckpoint;
            }

            state = RunState.Playing;
            Time.timeScale = 1f;
            ShowMessage($"Continue — {stageName}", 2f);
        }

        public void ApplyCharacter(CharacterType type)
        {
            selectedCharacter = type;
            if (player == null)
                return;

            CharacterTuning tuning = CharacterTuning.For(type);
            PlayerController2D controller = player.GetComponent<PlayerController2D>();
            CarrySystem2D carry = player.GetComponent<CarrySystem2D>();
            SpriteRenderer renderer = player.GetComponent<SpriteRenderer>();

            if (controller != null) controller.ApplyTuning(tuning);
            if (carry != null) carry.SetThrowHorizontalSpeed(tuning.ThrowSpeed);
            if (renderer != null) renderer.color = tuning.Color;
        }

        public void ShowMessage(string text, float seconds = 1.5f)
        {
            notificationText = text ?? string.Empty;
            notificationUntil = Time.unscaledTime + Mathf.Max(0.1f, seconds);
        }

        public void AddScore(int amount)
        {
            if (state != RunState.Playing)
                return;
            score = Mathf.Max(0, score + amount);
            PersistRun();
        }

        public void SetCheckpoint(Vector3 worldPosition)
        {
            checkpoint = worldPosition;
            CampaignSave.SaveCheckpoint(stageNumber, checkpoint);
            PersistRun();
            ShowMessage("Checkpoint saved", 1.6f);
        }

        public void PlayerDied()
        {
            if (state != RunState.Playing)
                return;

            CampaignSave.RecordDeath();
            lives--;
            if (lives <= 0)
            {
                CampaignSave.AbandonCampaign();
                state = RunState.GameOver;
                Time.timeScale = 0f;
                return;
            }

            PersistRun();
            RespawnPlayer();
        }

        public void RespawnPlayer()
        {
            if (player == null)
                return;

            Rigidbody2D body = player.GetComponent<Rigidbody2D>();
            if (body != null)
                body.linearVelocity = Vector2.zero;

            player.position = checkpoint;
            PlayerHealth health = player.GetComponent<PlayerHealth>();
            if (health != null)
                health.RestoreFull();

            ShowMessage($"Respawn  •  Lives: {lives}", 1.5f);
        }

        public void CompleteCurrentStage()
        {
            if (state != RunState.Playing)
                return;

            int bonus = stageDefinition != null ? stageDefinition.CompletionBonus : 2500;
            score += bonus;

            bool finalStage = stageDefinition == null || stageDefinition.FinalStage || stageNumber >= CampaignCatalog.StageCount;
            if (finalStage)
            {
                Win();
                return;
            }

            int nextStage = stageNumber + 1;
            string nextScene = !string.IsNullOrWhiteSpace(stageDefinition.NextSceneName)
                ? stageDefinition.NextSceneName
                : CampaignCatalog.SceneForStage(nextStage);

            CampaignSave.ClearCheckpoint();
            CampaignSave.SaveRun(selectedCharacter, nextStage, lives, score);
            CampaignRuntimeBridge.ResumeAfterSceneTransition = true;
            Time.timeScale = 1f;
            SceneManager.LoadScene(nextScene);
        }

        public void Win()
        {
            if (state != RunState.Playing)
                return;

            score += 5000;
            CampaignSave.RecordClear(score, selectedCharacter);
            state = RunState.Won;
            Time.timeScale = 0f;
        }

        public void RestartScene()
        {
            Time.timeScale = 1f;
            Scene active = SceneManager.GetActiveScene();
            if (active.buildIndex >= 0)
                SceneManager.LoadScene(active.buildIndex);
            else
                SceneManager.LoadScene(active.name);
        }

        private void PersistRun()
        {
            if (state == RunState.Playing)
                CampaignSave.SaveRun(selectedCharacter, stageNumber, lives, score);
        }

        private static void LoadStage(int number, bool resume)
        {
            Time.timeScale = 1f;
            CampaignRuntimeBridge.ResumeAfterSceneTransition = resume;
            SceneManager.LoadScene(CampaignCatalog.SceneForStage(number));
        }

        private void OnDestroy()
        {
            if (Instance == this)
            {
                Time.timeScale = 1f;
                Instance = null;
            }
        }
    }
}
