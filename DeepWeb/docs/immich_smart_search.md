# 此文档主要实现基于immich 的smart search 功能

## api 断点
https://api.immich.app/endpoints/search/searchSmart

## 请求示例

### 请求头
Request URL
http://127.0.0.1:2283/api/search/smart
Request Method
POST
Status Code
200 OK
Remote Address
127.0.0.1:2283
Referrer Policy
strict-origin-when-cross-origin

### 请求体
{
  "page": 1,
  "withExif": true,
  "isVisible": true,
  "language": "zh-CN",
  "query": "red clothes",
  "city": "Zhouxiang",
  "takenAfter": "2025-01-01T00:00:00.000Z",
  "takenBefore": "2025-12-11T23:59:59.999Z",
  "personIds": [
    "94777e17-bd75-4615-ac41-6f041b661af0",
    "8c9ce16f-433e-43a4-ab63-76769d39a00c"
  ]，
  “size”：5，     
}

### 响应格式

{
    "albums": {
        "total": 0,
        "count": 0,
        "items": [],
        "facets": []
    },
    "assets": {
        "total": 2,
        "count": 2,
        "items": [
            {
                "id": "ae1b5d90-a4fa-42a0-b0d0-e0a1d4add7ce",
                "createdAt": "2025-11-30T14:51:40.796Z",
                "deviceAssetId": "web-IMG_20251107_082344.jpg-1762475050000",
                "ownerId": "c985a427-cbfb-40bb-ac66-8eb3cab40b61",
                "deviceId": "WEB",
                "libraryId": null,
                "type": "IMAGE",
                "originalPath": "/data/library/admin/2025/2025-11-07/IMG_20251107_082344.jpg",
                "originalFileName": "IMG_20251107_082344.jpg",
                "originalMimeType": "image/jpeg",
                "thumbhash": "lzgKDYpAh3qQiJiYm2e3lWwItgWk",
                "fileCreatedAt": "2025-11-07T00:23:45.255Z",
                "fileModifiedAt": "2025-11-07T00:24:10.000Z",
                "localDateTime": "2025-11-07T08:23:45.255Z",
                "updatedAt": "2025-11-30T14:51:41.185Z",
                "isFavorite": false,
                "isArchived": false,
                "isTrashed": false,
                "visibility": "timeline",
                "duration": "0:00:00.00000",
                "exifInfo": {
                    "make": "HUAWEI",
                    "model": "NOH-AN00",
                    "exifImageWidth": 4160,
                    "exifImageHeight": 3120,
                    "fileSizeInByte": 3946844,
                    "orientation": "0",
                    "dateTimeOriginal": "2025-11-07T00:23:45.255+00:00",
                    "modifyDate": "2025-11-07T00:24:10+00:00",
                    "timeZone": "Asia/Shanghai",
                    "lensModel": null,
                    "fNumber": 2.4,
                    "focalLength": 2.7,
                    "iso": 50,
                    "exposureTime": "1/117",
                    "latitude": 30.179804,
                    "longitude": 121.121124,
                    "city": "Zhouxiang",
                    "state": "Zhejiang",
                    "country": "People's Republic of China",
                    "description": "",
                    "projectionType": null,
                    "rating": null
                },
                "livePhotoVideoId": null,
                "people": [
                    {
                        "id": "94777e17-bd75-4615-ac41-6f041b661af0",
                        "name": "Blue",
                        "birthDate": null,
                        "thumbnailPath": "/data/thumbs/c985a427-cbfb-40bb-ac66-8eb3cab40b61/94/77/94777e17-bd75-4615-ac41-6f041b661af0.jpeg",
                        "isHidden": false,
                        "isFavorite": false,
                        "updatedAt": "2025-11-30T14:53:33.041014+00:00",
                        "faces": [
                            {
                                "id": "057c3dc7-a0be-4bf4-96ba-6743bce14304",
                                "imageHeight": 1440,
                                "imageWidth": 1920,
                                "boundingBoxX1": 1122,
                                "boundingBoxX2": 1502,
                                "boundingBoxY1": 298,
                                "boundingBoxY2": 845,
                                "sourceType": "machine-learning"
                            }
                        ]
                    },
                    {
                        "id": "8c9ce16f-433e-43a4-ab63-76769d39a00c",
                        "name": "allison",
                        "birthDate": null,
                        "thumbnailPath": "/data/thumbs/c985a427-cbfb-40bb-ac66-8eb3cab40b61/8c/9c/8c9ce16f-433e-43a4-ab63-76769d39a00c.jpeg",
                        "isHidden": false,
                        "isFavorite": false,
                        "updatedAt": "2025-12-01T13:03:06.484648+00:00",
                        "faces": [
                            {
                                "id": "237b9d12-35fb-4bbc-bbdc-b2b209be2885",
                                "imageHeight": 1440,
                                "imageWidth": 1920,
                                "boundingBoxX1": 652,
                                "boundingBoxX2": 1131,
                                "boundingBoxY1": 279,
                                "boundingBoxY2": 913,
                                "sourceType": "machine-learning"
                            }
                        ]
                    }
                ],
                "unassignedFaces": [],
                "checksum": "dL8EAXTB4GXekwJepWhqIH6Nfhc=",
                "isOffline": false,
                "hasMetadata": true,
                "duplicateId": null,
                "resized": true
            },
            {
                "id": "7ae91db8-67b8-4358-a470-50e7eebe1e15",
                "createdAt": "2025-11-30T14:49:53.838Z",
                "deviceAssetId": "web-IMG_20251101_090543.jpg-1761959168000",
                "ownerId": "c985a427-cbfb-40bb-ac66-8eb3cab40b61",
                "deviceId": "WEB",
                "libraryId": null,
                "type": "IMAGE",
                "originalPath": "/data/library/admin/2025/2025-11-01/IMG_20251101_090543.jpg",
                "originalFileName": "IMG_20251101_090543.jpg",
                "originalMimeType": "image/jpeg",
                "thumbhash": "WggKDYJJPINklnWalfd1Vl16YFBJ",
                "fileCreatedAt": "2025-11-01T01:05:44.029Z",
                "fileModifiedAt": "2025-11-01T01:06:08.000Z",
                "localDateTime": "2025-11-01T09:05:44.029Z",
                "updatedAt": "2025-11-30T14:49:54.827Z",
                "isFavorite": false,
                "isArchived": false,
                "isTrashed": false,
                "visibility": "timeline",
                "duration": "0:00:00.00000",
                "exifInfo": {
                    "make": "HUAWEI",
                    "model": "NOH-AN00",
                    "exifImageWidth": 4160,
                    "exifImageHeight": 3120,
                    "fileSizeInByte": 4571640,
                    "orientation": "0",
                    "dateTimeOriginal": "2025-11-01T01:05:44.029+00:00",
                    "modifyDate": "2025-11-01T01:06:08+00:00",
                    "timeZone": "Asia/Shanghai",
                    "lensModel": null,
                    "fNumber": 2.4,
                    "focalLength": 2.7,
                    "iso": 50,
                    "exposureTime": "1/138",
                    "latitude": 30.18327,
                    "longitude": 121.136948,
                    "city": "Zhouxiang",
                    "state": "Zhejiang",
                    "country": "People's Republic of China",
                    "description": "",
                    "projectionType": null,
                    "rating": null
                },
                "livePhotoVideoId": null,
                "people": [
                    {
                        "id": "8337ede5-5662-4d3f-ba11-f9f2d4b511ce",
                        "name": "Susan",
                        "birthDate": null,
                        "thumbnailPath": "/data/thumbs/c985a427-cbfb-40bb-ac66-8eb3cab40b61/83/37/8337ede5-5662-4d3f-ba11-f9f2d4b511ce.jpeg",
                        "isHidden": false,
                        "isFavorite": false,
                        "updatedAt": "2025-11-30T14:54:28.183576+00:00",
                        "faces": [
                            {
                                "id": "3dfe6ab2-6a99-4354-a4cb-311f32f0206a",
                                "imageHeight": 1440,
                                "imageWidth": 1920,
                                "boundingBoxX1": 731,
                                "boundingBoxX2": 1033,
                                "boundingBoxY1": 173,
                                "boundingBoxY2": 572,
                                "sourceType": "machine-learning"
                            }
                        ]
                    },
                    {
                        "id": "94777e17-bd75-4615-ac41-6f041b661af0",
                        "name": "Blue",
                        "birthDate": null,
                        "thumbnailPath": "/data/thumbs/c985a427-cbfb-40bb-ac66-8eb3cab40b61/94/77/94777e17-bd75-4615-ac41-6f041b661af0.jpeg",
                        "isHidden": false,
                        "isFavorite": false,
                        "updatedAt": "2025-11-30T14:53:33.041014+00:00",
                        "faces": [
                            {
                                "id": "1ad16e1d-f225-49f4-8f97-f3e7ed5df792",
                                "imageHeight": 1440,
                                "imageWidth": 1920,
                                "boundingBoxX1": 1111,
                                "boundingBoxX2": 1430,
                                "boundingBoxY1": 590,
                                "boundingBoxY2": 1034,
                                "sourceType": "machine-learning"
                            }
                        ]
                    },
                    {
                        "id": "8c9ce16f-433e-43a4-ab63-76769d39a00c",
                        "name": "allison",
                        "birthDate": null,
                        "thumbnailPath": "/data/thumbs/c985a427-cbfb-40bb-ac66-8eb3cab40b61/8c/9c/8c9ce16f-433e-43a4-ab63-76769d39a00c.jpeg",
                        "isHidden": false,
                        "isFavorite": false,
                        "updatedAt": "2025-12-01T13:03:06.484648+00:00",
                        "faces": [
                            {
                                "id": "a57676f7-30f0-4281-98aa-300f95acb75e",
                                "imageHeight": 1440,
                                "imageWidth": 1920,
                                "boundingBoxX1": 755,
                                "boundingBoxX2": 1087,
                                "boundingBoxY1": 782,
                                "boundingBoxY2": 1175,
                                "sourceType": "machine-learning"
                            }
                        ]
                    }
                ],
                "unassignedFaces": [],
                "checksum": "OOmE/t7Ks/iKNikqifF73e8/dBA=",
                "isOffline": false,
                "hasMetadata": true,
                "duplicateId": null,
                "resized": true
            }
        ],
        "facets": [],
        "nextPage": null
    }
}

## 需求
- 异步请求


## 参考api
(env_web) (deepweb) hanli@hanlideMacBook-Air deepweb %  uv pip install immich-python-sdk
Using Python 3.12.12 environment at: env_web
Resolved 9 packages in 2.20s
Prepared 1 package in 2.01s
Installed 1 package in 5ms
 + immich-python-sdk==1.134.0
(env_web) (deepweb) hanli@hanlideMacBook-Air deepweb % python
Python 3.12.12 | packaged by Anaconda, Inc. | (main, Oct 21 2025, 20:07:49) [Clang 20.1.8 ] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import immich_python_sdk
print(dir(immich_python_sdk))  # 列出模块>>> print(dir(immich_python_sdk))  # 列出模块
['APIKeyCreateDto', 'APIKeyCreateResponseDto', 'APIKeyResponseDto', 'APIKeyUpdateDto', 'APIKeysApi', 'ActivitiesApi', 'ActivityCreateDto', 'ActivityResponseDto', 'ActivityStatisticsResponseDto', 'AddUsersDto', 'AdminOnboardingUpdateDto', 'AlbumResponseDto', 'AlbumStatisticsResponseDto', 'AlbumUserAddDto', 'AlbumUserCreateDto', 'AlbumUserResponseDto', 'AlbumUserRole', 'AlbumsApi', 'AllJobStatusResponseDto', 'ApiAttributeError', 'ApiClient', 'ApiException', 'ApiKeyError', 'ApiResponse', 'ApiTypeError', 'ApiValueError', 'AssetBulkDeleteDto', 'AssetBulkUpdateDto', 'AssetBulkUploadCheckDto', 'AssetBulkUploadCheckItem', 'AssetBulkUploadCheckResponseDto', 'AssetBulkUploadCheckResult', 'AssetDeltaSyncDto', 'AssetDeltaSyncResponseDto', 'AssetFaceCreateDto', 'AssetFaceDeleteDto', 'AssetFaceResponseDto', 'AssetFaceUpdateDto', 'AssetFaceUpdateItem', 'AssetFaceWithoutPersonResponseDto', 'AssetFullSyncDto', 'AssetIdsDto', 'AssetIdsResponseDto', 'AssetJobName', 'AssetJobsDto', 'AssetMediaResponseDto', 'AssetMediaSize', 'AssetMediaStatus', 'AssetOrder', 'AssetResponseDto', 'AssetStackResponseDto', 'AssetStatsResponseDto', 'AssetTypeEnum', 'AssetVisibility', 'AssetsApi', 'AudioCodec', 'AuthStatusResponseDto', 'AuthenticationApi', 'AvatarUpdate', 'BulkIdResponseDto', 'BulkIdsDto', 'CLIPConfig', 'CQMode', 'ChangePasswordDto', 'CheckExistingAssetsDto', 'CheckExistingAssetsResponseDto', 'Colorspace', 'Configuration', 'CreateAlbumDto', 'CreateLibraryDto', 'CreateProfileImageResponseDto', 'DatabaseBackupConfig', 'DeprecatedApi', 'DownloadApi', 'DownloadArchiveInfo', 'DownloadInfoDto', 'DownloadResponse', 'DownloadResponseDto', 'DownloadUpdate', 'DuplicateDetectionConfig', 'DuplicateResponseDto', 'DuplicatesApi', 'EmailNotificationsResponse', 'EmailNotificationsUpdate', 'ExifResponseDto', 'FaceDto', 'FacesApi', 'FacialRecognitionConfig', 'FoldersResponse', 'FoldersUpdate', 'ImageFormat', 'JobCommand', 'JobCommandDto', 'JobCountsDto', 'JobCreateDto', 'JobName', 'JobSettingsDto', 'JobStatusDto', 'JobsApi', 'LibrariesApi', 'LibraryResponseDto', 'LibraryStatsResponseDto', 'LicenseKeyDto', 'LicenseResponseDto', 'LogLevel', 'LoginCredentialDto', 'LoginResponseDto', 'LogoutResponseDto', 'ManualJobName', 'MapApi', 'MapMarkerResponseDto', 'MapReverseGeocodeResponseDto', 'MemoriesApi', 'MemoriesResponse', 'MemoriesUpdate', 'MemoryCreateDto', 'MemoryResponseDto', 'MemoryType', 'MemoryUpdateDto', 'MergePersonDto', 'MetadataSearchDto', 'NotificationCreateDto', 'NotificationDeleteAllDto', 'NotificationDto', 'NotificationLevel', 'NotificationType', 'NotificationUpdateAllDto', 'NotificationUpdateDto', 'NotificationsAdminApi', 'NotificationsApi', 'OAuthApi', 'OAuthAuthorizeResponseDto', 'OAuthCallbackDto', 'OAuthConfigDto', 'OAuthTokenEndpointAuthMethod', 'OnThisDayDto', 'OpenApiException', 'PartnerDirection', 'PartnerResponseDto', 'PartnersApi', 'PeopleApi', 'PeopleResponse', 'PeopleResponseDto', 'PeopleUpdate', 'PeopleUpdateDto', 'PeopleUpdateItem', 'Permission', 'PersonCreateDto', 'PersonResponseDto', 'PersonStatisticsResponseDto', 'PersonUpdateDto', 'PersonWithFacesResponseDto', 'PinCodeChangeDto', 'PinCodeResetDto', 'PinCodeSetupDto', 'PlacesResponseDto', 'PurchaseResponse', 'PurchaseUpdate', 'QueueStatusDto', 'RandomSearchDto', 'RatingsResponse', 'RatingsUpdate', 'ReactionLevel', 'ReactionType', 'ReverseGeocodingStateResponseDto', 'SearchAlbumResponseDto', 'SearchApi', 'SearchAssetResponseDto', 'SearchExploreItem', 'SearchExploreResponseDto', 'SearchFacetCountResponseDto', 'SearchFacetResponseDto', 'SearchResponseDto', 'SearchSuggestionType', 'ServerAboutResponseDto', 'ServerApi', 'ServerConfigDto', 'ServerFeaturesDto', 'ServerMediaTypesResponseDto', 'ServerPingResponse', 'ServerStatsResponseDto', 'ServerStorageResponseDto', 'ServerThemeDto', 'ServerVersionHistoryResponseDto', 'ServerVersionResponseDto', 'SessionCreateDto', 'SessionCreateResponseDto', 'SessionResponseDto', 'SessionUnlockDto', 'SessionsApi', 'SharedLinkCreateDto', 'SharedLinkEditDto', 'SharedLinkResponseDto', 'SharedLinkType', 'SharedLinksApi', 'SharedLinksResponse', 'SharedLinksUpdate', 'SignUpDto', 'SmartSearchDto', 'SourceType', 'StackCreateDto', 'StackResponseDto', 'StackUpdateDto', 'StacksApi', 'SyncAckDeleteDto', 'SyncAckDto', 'SyncAckSetDto', 'SyncAlbumDeleteV1', 'SyncAlbumUserDeleteV1', 'SyncAlbumUserV1', 'SyncAlbumV1', 'SyncApi', 'SyncAssetDeleteV1', 'SyncAssetExifV1', 'SyncAssetV1', 'SyncEntityType', 'SyncPartnerDeleteV1', 'SyncPartnerV1', 'SyncRequestType', 'SyncStreamDto', 'SyncUserDeleteV1', 'SyncUserV1', 'SystemConfigApi', 'SystemConfigBackupsDto', 'SystemConfigDto', 'SystemConfigFFmpegDto', 'SystemConfigFacesDto', 'SystemConfigGeneratedFullsizeImageDto', 'SystemConfigGeneratedImageDto', 'SystemConfigImageDto', 'SystemConfigJobDto', 'SystemConfigLibraryDto', 'SystemConfigLibraryScanDto', 'SystemConfigLibraryWatchDto', 'SystemConfigLoggingDto', 'SystemConfigMachineLearningDto', 'SystemConfigMapDto', 'SystemConfigMetadataDto', 'SystemConfigNewVersionCheckDto', 'SystemConfigNotificationsDto', 'SystemConfigOAuthDto', 'SystemConfigPasswordLoginDto', 'SystemConfigReverseGeocodingDto', 'SystemConfigServerDto', 'SystemConfigSmtpDto', 'SystemConfigSmtpTransportDto', 'SystemConfigStorageTemplateDto', 'SystemConfigTemplateEmailsDto', 'SystemConfigTemplateStorageOptionDto', 'SystemConfigTemplatesDto', 'SystemConfigThemeDto', 'SystemConfigTrashDto', 'SystemConfigUserDto', 'SystemMetadataApi', 'TagBulkAssetsDto', 'TagBulkAssetsResponseDto', 'TagCreateDto', 'TagResponseDto', 'TagUpdateDto', 'TagUpsertDto', 'TagsApi', 'TagsResponse', 'TagsUpdate', 'TemplateDto', 'TemplateResponseDto', 'TestEmailResponseDto', 'TimeBucketAssetResponseDto', 'TimeBucketsResponseDto', 'TimelineApi', 'ToneMapping', 'TranscodeHWAccel', 'TranscodePolicy', 'TrashApi', 'TrashResponseDto', 'UpdateAlbumDto', 'UpdateAlbumUserDto', 'UpdateAssetDto', 'UpdateLibraryDto', 'UpdatePartnerDto', 'UsageByUserDto', 'UserAdminCreateDto', 'UserAdminDeleteDto', 'UserAdminResponseDto', 'UserAdminUpdateDto', 'UserAvatarColor', 'UserLicense', 'UserPreferencesResponseDto', 'UserPreferencesUpdateDto', 'UserResponseDto', 'UserStatus', 'UserUpdateMeDto', 'UsersAdminApi', 'UsersApi', 'ValidateAccessTokenResponseDto', 'ValidateLibraryDto', 'ValidateLibraryImportPathResponseDto', 'ValidateLibraryResponseDto', 'VersionCheckStateResponseDto', 'VideoCodec', 'VideoContainer', 'ViewApi', '__all__', '__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__path__', '__spec__', '__version__', 'api', 'api_client', 'api_response', 'configuration', 'exceptions', 'models', 'rest']
