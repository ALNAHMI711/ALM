using System;
using UnityEngine;

namespace YOW.Core
{
    public static class InstallationIdentity
    {
        private const string Key = "YOW.InstallationId";

        public static string GetOrCreate()
        {
            var value = PlayerPrefs.GetString(Key, "");
            if (!string.IsNullOrWhiteSpace(value))
                return value;

            value = Guid.NewGuid().ToString("N");
            PlayerPrefs.SetString(Key, value);
            PlayerPrefs.Save();
            return value;
        }
    }
}
