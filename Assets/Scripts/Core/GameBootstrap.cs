using UnityEngine;

namespace YOW.Core
{
    public sealed class GameBootstrap : MonoBehaviour
    {
        [SerializeField] private ContentManifestLoader contentLoader;

        private void Awake()
        {
            DontDestroyOnLoad(gameObject);
            Application.targetFrameRate = 60;
            QualitySettings.vSyncCount = 0;
        }

        private async void Start()
        {
            if (contentLoader != null)
                await contentLoader.InitializeAsync();
        }
    }
}
