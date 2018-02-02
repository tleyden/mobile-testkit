﻿// 
//  Router.cs
// 
//  Author:
//   Jim Borden  <jim.borden@couchbase.com>
// 
//  Copyright (c) 2017 Couchbase, Inc All rights reserved.
// 
//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at
// 
//  http://www.apache.org/licenses/LICENSE-2.0
// 
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.
// 

using System;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Text;

using JetBrains.Annotations;

using Newtonsoft.Json;

using HandlerAction = System.Action<System.Collections.Specialized.NameValueCollection,
    System.Collections.Generic.IReadOnlyDictionary<string, object>,
    System.Net.HttpListenerResponse>;

namespace Couchbase.Lite.Testing
{
    public static class Router
    {
        #region Constants

        [NotNull]
        private static readonly IDictionary<string, HandlerAction> RouteMap =
            new Dictionary<string, HandlerAction>
            {
            ["basicAuthenticator_creaate"] = BasicAuthenticationMethods.Create,
            ["sessionAuthenticator_create"] = SessionAuthenticationMethods.Create,
            ["databaseConfiguration_configure"] = DatabaseConfigurationMethods.Configure,
            ["database_create"] = DatabaseMethods.DatabaseCreate,
            ["database_close"] = DatabaseMethods.DatabaseClose,
            ["database_getPath"] = DatabaseMethods.DatabasePath,
            ["database_deleteDB"] = DatabaseMethods.DatabaseDeleteDB,
            ["database_delete"] = DatabaseMethods.DatabaseDelete,
            ["database_getName"] = DatabaseMethods.DatabaseGetName,
            ["database_getDocument"] = DatabaseMethods.DatabaseGetDocument,
            ["database_saveDocuments"] = DatabaseMethods.DatabaseSaveDocuments,
            ["database_purge"] = DatabaseMethods.DatabasePurge,
            ["database_save"] = DatabaseMethods.DatabaseSave,
            ["database_getCount"] = DatabaseMethods.DatabaseGetCount,
            ["databaseChangeListener_changesCount"] = DatabaseMethods.DatabaseChangeListenerChangesCount,
            ["databaseChangeListener_getChange"] = DatabaseMethods.DatabaseChangeListenerGetChange,
            ["databaseChange_getDocumentId"] = DatabaseMethods.DatabaseChangeGetDocumentId,
            ["database_addDocuments"] = DatabaseMethods.DatabaseAddDocuments,
            ["database_getDocIds"] = DatabaseMethods.DatabaseGetDocIds,
            ["database_getDocuments"] = DatabaseMethods.DatabaseGetDocuments,
            ["document_create"] = DocumentMethods.DocumentCreate,
            ["document_delete"] = DocumentMethods.DocumentDelete,
            ["document_getId"] = DocumentMethods.DocumentGetId,
            ["document_getString"] = DocumentMethods.DocumentGetString,
            ["document_setString"] = DocumentMethods.DocumentSetString,
            ["replicatorConfiguration_configure"] = ReplicatorConfigurationMethods.Configure,
            ["replicator_create"] = ReplicationMethods.Create,
            ["replicator_getActivityLevel"] = ReplicationMethods.GetActivityLevel,
            ["replicator_getError"] = ReplicationMethods.GetError,
            ["replicator_getTotal"] = ReplicationMethods.GetTotal,
            ["replicator_getConfig"] = ReplicationMethods.GetConfig,
            ["replicatorConfiguration_setAuthenticator"] = ReplicatorConfigurationMethods.SetAuthenticator,
            ["configure_replication"] = ReplicatorConfigurationMethods.Configure,
            ["start_replication"] = ReplicationMethods.StartReplication,
            ["stop_replication"] = ReplicationMethods.StopReplication,
            ["replication_getStatus"] = ReplicationMethods.Status,
            ["release"] = ReleaseObject
            };

        #endregion

        #region Public Methods

        public static void Extend([NotNull]IDictionary<string, HandlerAction> extensions)
        {
            foreach (var pair in extensions)
            {
                if (!RouteMap.ContainsKey(pair.Key))
                {
                    RouteMap[pair.Key] = pair.Value;
                }
            }
        }

        #endregion

        #region Internal Methods

        internal static void Handle([NotNull]Uri endpoint, [NotNull]Stream body, [NotNull]HttpListenerResponse response)
        {
            if (!RouteMap.TryGetValue(endpoint.AbsolutePath?.TrimStart('/'), out HandlerAction action))
            {
                response.WriteEmptyBody(HttpStatusCode.NotFound);
                return;
            }


            Dictionary<string, string> jsonObj;
            Dictionary<string, object> bodyObj;
            try
            {
                var serializer = JsonSerializer.CreateDefault();
                using (var reader = new JsonTextReader(new StreamReader(body, Encoding.UTF8, false, 8192, false)))
                {
                    reader.CloseInput = true;
                    jsonObj = serializer?.Deserialize<Dictionary<string, string>>(reader) ?? new Dictionary<string, string>();
                    bodyObj = ValueSerializer.Deserialize(jsonObj);
                }
            }
            catch (Exception e)
            {
                Debug.WriteLine($"Error deserializing POST body for {endpoint}: {e}");
                Console.WriteLine($"Error deserializing POST body for {endpoint}: {e.Message}");
                response.WriteBody("Invalid JSON body received");
                return;
            }

            var args = endpoint.ParseQueryString();
            try
            {
                action(args, bodyObj, response);
            }
            catch (Exception e)
            {
                Debug.WriteLine($"Error in handler for {endpoint}: {e}");
                Console.WriteLine($"Error in handler for {endpoint}: {e.Message}");
                response.WriteBody(e.Message?.Replace("\r", "")?.Replace('\n', ' ') ?? String.Empty, false);
            }
        }

        #endregion

        #region Private Methods

        private static void ReleaseObject([NotNull]NameValueCollection args,
            [NotNull]IReadOnlyDictionary<string, object> postBody,
            [NotNull]HttpListenerResponse response)
        {
            var id = postBody["object"].ToString();
            MemoryMap.Release(id);
        }

        #endregion
    }
}