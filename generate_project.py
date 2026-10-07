#!/usr/bin/env python3
import hashlib
import os
from pathlib import Path


def uid(name: str) -> str:
    """Generate consistent 24-character hexadecimal Xcode identifier."""
    return hashlib.md5(name.encode("utf-8")).hexdigest()[:24].upper()


def generate_pbxproj(project_dir: Path):
    proj_name = "OpenRouterTracker"
    app_target_name = "OpenRouterTracker"
    widget_target_name = "OpenRouterWidgetExtension"

    # UUIDs
    proj_id = uid("PBXProject")
    main_group_id = uid("MainGroup")
    products_group_id = uid("ProductsGroup")
    shared_group_id = uid("SharedGroup")
    app_group_id = uid("AppGroup")
    widget_group_id = uid("WidgetGroup")

    app_product_id = uid("AppProduct")
    widget_product_id = uid("WidgetProduct")

    # Files
    shared_files = [
        ("OpenRouterModel.swift", uid("File_OpenRouterModel")),
        ("OpenRouterService.swift", uid("File_OpenRouterService")),
        ("SharedStorage.swift", uid("File_SharedStorage")),
        ("KeychainHelper.swift", uid("File_KeychainHelper")),
    ]

    app_files = [
        ("OpenRouterTrackerApp.swift", uid("File_OpenRouterTrackerApp")),
        ("ContentView.swift", uid("File_ContentView")),
        ("Info.plist", uid("File_App_InfoPlist")),
        ("OpenRouterTracker.entitlements", uid("File_App_Entitlements")),
    ]

    widget_files = [
        ("OpenRouterWidgetBundle.swift", uid("File_OpenRouterWidgetBundle")),
        ("OpenRouterWidget.swift", uid("File_OpenRouterWidget")),
        ("OpenRouterWidgetView.swift", uid("File_OpenRouterWidgetView")),
        ("RefreshBalanceIntent.swift", uid("File_RefreshBalanceIntent")),
        ("Info.plist", uid("File_Widget_InfoPlist")),
        ("OpenRouterWidget.entitlements", uid("File_Widget_Entitlements")),
    ]

    # Build files (Sources)
    app_build_sources = []
    for name, fid in shared_files:
        bfid = uid(f"AppBuild_{name}")
        app_build_sources.append((fid, bfid, name))
    for name, fid in app_files:
        if name.endswith(".swift"):
            bfid = uid(f"AppBuild_{name}")
            app_build_sources.append((fid, bfid, name))

    widget_build_sources = []
    for name, fid in shared_files:
        bfid = uid(f"WidgetBuild_{name}")
        widget_build_sources.append((fid, bfid, name))
    for name, fid in widget_files:
        if name.endswith(".swift"):
            bfid = uid(f"WidgetBuild_{name}")
            widget_build_sources.append((fid, bfid, name))

    # Embed extension build file
    embed_widget_bfid = uid("Embed_Widget_BuildFile")

    # Target IDs
    app_target_id = uid("Target_App")
    widget_target_id = uid("Target_Widget")

    # Target Dependency IDs
    target_dep_id = uid("TargetDep_Widget")
    container_proxy_id = uid("ContainerProxy_Widget")

    # Build Phases
    app_sources_phase_id = uid("Phase_App_Sources")
    app_frameworks_phase_id = uid("Phase_App_Frameworks")
    app_resources_phase_id = uid("Phase_App_Resources")
    app_embed_phase_id = uid("Phase_App_Embed_Widget")

    widget_sources_phase_id = uid("Phase_Widget_Sources")
    widget_frameworks_phase_id = uid("Phase_Widget_Frameworks")
    widget_resources_phase_id = uid("Phase_Widget_Resources")

    # Configs
    proj_cfg_list_id = uid("CfgList_Project")
    proj_cfg_debug_id = uid("Cfg_Project_Debug")
    proj_cfg_release_id = uid("Cfg_Project_Release")

    app_cfg_list_id = uid("CfgList_App")
    app_cfg_debug_id = uid("Cfg_App_Debug")
    app_cfg_release_id = uid("Cfg_App_Release")

    widget_cfg_list_id = uid("CfgList_Widget")
    widget_cfg_debug_id = uid("Cfg_Widget_Debug")
    widget_cfg_release_id = uid("Cfg_Widget_Release")

    # Compose project.pbxproj
    content = f"""// !$*UTF8*$!
{{
	archiveVersion = 1;
	classes = {{
	}};
	objectVersion = 56;
	objects = {{

/* Begin PBXBuildFile section */
"""
    for fid, bfid, name in app_build_sources:
        content += f"\t\t{bfid} /* {name} in Sources */ = {{isa = PBXBuildFile; fileRef = {fid} /* {name} */; }};\n"
    for fid, bfid, name in widget_build_sources:
        content += f"\t\t{bfid} /* {name} in Sources */ = {{isa = PBXBuildFile; fileRef = {fid} /* {name} */; }};\n"
    content += f"\t\t{embed_widget_bfid} /* OpenRouterWidgetExtension.appex in PlugIns */ = {{isa = PBXBuildFile; fileRef = {widget_product_id} /* OpenRouterWidgetExtension.appex */; settings = {{ATTRIBUTES = (RemoveHeadersOnCopy, ); }}; }};\n"

    content += """/* End PBXBuildFile section */

/* Begin PBXContainerItemProxy section */
"""
    content += f"""\t\t{container_proxy_id} /* PBXContainerItemProxy */ = {{
			isa = PBXContainerItemProxy;
			containerPortal = {proj_id} /* Project object */;
			proxyType = 1;
			remoteGlobalIDString = {widget_target_id};
			remoteInfo = OpenRouterWidgetExtension;
		}};
/* End PBXContainerItemProxy section */

/* Begin PBXCopyFilesBuildPhase section */
\t\t{app_embed_phase_id} /* Embed PlugIns */ = {{
			isa = PBXCopyFilesBuildPhase;
			buildActionMask = 2147483647;
			dstPath = "";
			dstSubfolderSpec = 13;
			files = (
				{embed_widget_bfid} /* OpenRouterWidgetExtension.appex in PlugIns */,
			);
			name = "Embed PlugIns";
			runOnlyForDeploymentPostprocessing = 0;
		}};
/* End PBXCopyFilesBuildPhase section */

/* Begin PBXFileReference section */
\t\t{app_product_id} /* OpenRouterTracker.app */ = {{isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = OpenRouterTracker.app; sourceTree = BUILT_PRODUCTS_DIR; }};
\t\t{widget_product_id} /* OpenRouterWidgetExtension.appex */ = {{isa = PBXFileReference; explicitFileType = "wrapper.app-extension"; includeInIndex = 0; path = OpenRouterWidgetExtension.appex; sourceTree = BUILT_PRODUCTS_DIR; }};
"""

    for name, fid in shared_files:
        content += f"\t\t{fid} /* {name} */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = {name}; sourceTree = \"<group>\"; }};\n"
    for name, fid in app_files:
        ftype = "sourcecode.swift" if name.endswith(".swift") else ("text.plist.xml" if name.endswith(".plist") else "text.plist.entitlements")
        content += f"\t\t{fid} /* {name} */ = {{isa = PBXFileReference; lastKnownFileType = {ftype}; path = {name}; sourceTree = \"<group>\"; }};\n"
    for name, fid in widget_files:
        ftype = "sourcecode.swift" if name.endswith(".swift") else ("text.plist.xml" if name.endswith(".plist") else "text.plist.entitlements")
        content += f"\t\t{fid} /* {name} */ = {{isa = PBXFileReference; lastKnownFileType = {ftype}; path = {name}; sourceTree = \"<group>\"; }};\n"

    content += f"""/* End PBXFileReference section */

/* Begin PBXFrameworksBuildPhase section */
\t\t{app_frameworks_phase_id} /* Frameworks */ = {{
			isa = PBXFrameworksBuildPhase;
			buildActionMask = 2147483647;
			files = (
			);
			runOnlyForDeploymentPostprocessing = 0;
		}};
\t\t{widget_frameworks_phase_id} /* Frameworks */ = {{
			isa = PBXFrameworksBuildPhase;
			buildActionMask = 2147483647;
			files = (
			);
			runOnlyForDeploymentPostprocessing = 0;
		}};
/* End PBXFrameworksBuildPhase section */

/* Begin PBXGroup section */
\t\t{main_group_id} = {{
			isa = PBXGroup;
			children = (
				{shared_group_id} /* Shared */,
				{app_group_id} /* OpenRouterTrackerApp */,
				{widget_group_id} /* OpenRouterWidgetExtension */,
				{products_group_id} /* Products */,
			);
			sourceTree = "<group>";
		}};
\t\t{products_group_id} /* Products */ = {{
			isa = PBXGroup;
			children = (
				{app_product_id} /* OpenRouterTracker.app */,
				{widget_product_id} /* OpenRouterWidgetExtension.appex */,
			);
			name = Products;
			sourceTree = "<group>";
		}};
\t\t{shared_group_id} /* Shared */ = {{
			isa = PBXGroup;
			children = (
"""
    for name, fid in shared_files:
        content += f"\t\t\t\t{fid} /* {name} */,\n"
    content += f"""\t\t\t);
			path = Shared;
			sourceTree = "<group>";
		}};
\t\t{app_group_id} /* OpenRouterTrackerApp */ = {{
			isa = PBXGroup;
			children = (
"""
    for name, fid in app_files:
        content += f"\t\t\t\t{fid} /* {name} */,\n"
    content += f"""\t\t\t);
			path = OpenRouterTrackerApp;
			sourceTree = "<group>";
		}};
\t\t{widget_group_id} /* OpenRouterWidgetExtension */ = {{
			isa = PBXGroup;
			children = (
"""
    for name, fid in widget_files:
        content += f"\t\t\t\t{fid} /* {name} */,\n"
    content += f"""\t\t\t);
			path = OpenRouterWidgetExtension;
			sourceTree = "<group>";
		}};
/* End PBXGroup section */

/* Begin PBXNativeTarget section */
\t\t{app_target_id} /* {app_target_name} */ = {{
			isa = PBXNativeTarget;
			buildConfigurationList = {app_cfg_list_id} /* Build configuration list for PBXNativeTarget "{app_target_name}" */;
			buildPhases = (
				{app_sources_phase_id} /* Sources */,
				{app_frameworks_phase_id} /* Frameworks */,
				{app_resources_phase_id} /* Resources */,
				{app_embed_phase_id} /* Embed PlugIns */,
			);
			buildRules = (
			);
			dependencies = (
				{target_dep_id} /* PBXTargetDependency */,
			);
			name = {app_target_name};
			productName = {app_target_name};
			productReference = {app_product_id} /* OpenRouterTracker.app */;
			productType = "com.apple.product-type.application";
		}};
\t\t{widget_target_id} /* {widget_target_name} */ = {{
			isa = PBXNativeTarget;
			buildConfigurationList = {widget_cfg_list_id} /* Build configuration list for PBXNativeTarget "{widget_target_name}" */;
			buildPhases = (
				{widget_sources_phase_id} /* Sources */,
				{widget_frameworks_phase_id} /* Frameworks */,
				{widget_resources_phase_id} /* Resources */,
			);
			buildRules = (
			);
			dependencies = (
			);
			name = {widget_target_name};
			productName = {widget_target_name};
			productReference = {widget_product_id} /* OpenRouterWidgetExtension.appex */;
			productType = "com.apple.product-type.app-extension";
		}};
/* End PBXNativeTarget section */

/* Begin PBXProject section */
\t\t{proj_id} /* Project object */ = {{
			isa = PBXProject;
			attributes = {{
				BuildIndependentTargetsInParallel = 1;
				LastSwiftUpdateCheck = 1500;
				LastUpgradeCheck = 1500;
				TargetAttributes = {{
					{app_target_id} = {{
						CreatedOnToolsVersion = 15.0;
					}};
					{widget_target_id} = {{
						CreatedOnToolsVersion = 15.0;
					}};
				}};
			}};
			buildConfigurationList = {proj_cfg_list_id} /* Build configuration list for PBXProject "{proj_name}" */;
			compatibilityVersion = "Xcode 14.0";
			developmentRegion = en;
			hasScannedForEncodings = 0;
			knownRegions = (
				en,
				Base,
			);
			mainGroup = {main_group_id};
			productRefGroup = {products_group_id} /* Products */;
			projectDirPath = "";
			projectRoot = "";
			targets = (
				{app_target_id} /* {app_target_name} */,
				{widget_target_id} /* {widget_target_name} */,
			);
		}};
/* End PBXProject section */

/* Begin PBXResourcesBuildPhase section */
\t\t{app_resources_phase_id} /* Resources */ = {{
			isa = PBXResourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
			);
			runOnlyForDeploymentPostprocessing = 0;
		}};
\t\t{widget_resources_phase_id} /* Resources */ = {{
			isa = PBXResourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
			);
			runOnlyForDeploymentPostprocessing = 0;
		}};
/* End PBXResourcesBuildPhase section */

/* Begin PBXSourcesBuildPhase section */
\t\t{app_sources_phase_id} /* Sources */ = {{
			isa = PBXSourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
"""
    for fid, bfid, name in app_build_sources:
        content += f"\t\t\t\t{bfid} /* {name} in Sources */,\n"
    content += f"""\t\t\t);
			runOnlyForDeploymentPostprocessing = 0;
		}};
\t\t{widget_sources_phase_id} /* Sources */ = {{
			isa = PBXSourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
"""
    for fid, bfid, name in widget_build_sources:
        content += f"\t\t\t\t{bfid} /* {name} in Sources */,\n"
    content += f"""\t\t\t);
			runOnlyForDeploymentPostprocessing = 0;
		}};
/* End PBXSourcesBuildPhase section */

/* Begin PBXTargetDependency section */
\t\t{target_dep_id} /* PBXTargetDependency */ = {{
			isa = PBXTargetDependency;
			target = {widget_target_id} /* {widget_target_name} */;
			targetProxy = {container_proxy_id} /* PBXContainerItemProxy */;
		}};
/* End PBXTargetDependency section */

/* Begin XCBuildConfiguration section */
\t\t{proj_cfg_debug_id} /* Debug */ = {{
			isa = XCBuildConfiguration;
			buildSettings = {{
				ALWAYS_SEARCH_USER_PATHS = NO;
				CLANG_ANALYZER_NONNULL = YES;
				CLANG_CXX_LANGUAGE_STANDARD = "gnu++20";
				CLANG_ENABLE_MODULES = YES;
				CLANG_ENABLE_OBJC_ARC = YES;
				COPY_PHASE_STRIP = NO;
				DEBUG_INFORMATION_FORMAT = dwarf;
				ENABLE_STRICT_OBJC_MSGSEND = YES;
				ENABLE_TESTABILITY = YES;
				GCC_OPTIMIZATION_LEVEL = 0;
				MACOSX_DEPLOYMENT_TARGET = 14.0;
				MTL_ENABLE_DEBUG_INFO = INCLUDE_SOURCE;
				ONLY_ACTIVE_ARCH = YES;
				SDKROOT = macosx;
				SWIFT_ACTIVE_COMPILATION_CONDITIONS = DEBUG;
				SWIFT_OPTIMIZATION_LEVEL = "-Onone";
				SWIFT_VERSION = 5.0;
			}};
			name = Debug;
		}};
\t\t{proj_cfg_release_id} /* Release */ = {{
			isa = XCBuildConfiguration;
			buildSettings = {{
				ALWAYS_SEARCH_USER_PATHS = NO;
				CLANG_ANALYZER_NONNULL = YES;
				CLANG_CXX_LANGUAGE_STANDARD = "gnu++20";
				CLANG_ENABLE_MODULES = YES;
				CLANG_ENABLE_OBJC_ARC = YES;
				COPY_PHASE_STRIP = NO;
				DEBUG_INFORMATION_FORMAT = "dwarf-with-dsym";
				ENABLE_NS_ASSERTIONS = NO;
				ENABLE_STRICT_OBJC_MSGSEND = YES;
				GCC_OPTIMIZATION_LEVEL = s;
				MACOSX_DEPLOYMENT_TARGET = 14.0;
				MTL_ENABLE_DEBUG_INFO = NO;
				SDKROOT = macosx;
				SWIFT_COMPILATION_MODE = wholemodule;
				SWIFT_OPTIMIZATION_LEVEL = "-O";
				SWIFT_VERSION = 5.0;
			}};
			name = Release;
		}};
\t\t{app_cfg_debug_id} /* Debug */ = {{
			isa = XCBuildConfiguration;
			buildSettings = {{
				ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;
				CODE_SIGN_IDENTITY = "-";
				CODE_SIGN_STYLE = Manual;
				CODE_SIGN_ENTITLEMENTS = OpenRouterTrackerApp/OpenRouterTracker.entitlements;
				COMBINE_HIDPI_IMAGES = YES;
				GENERATE_INFOPLIST_FILE = NO;
				INFOPLIST_FILE = OpenRouterTrackerApp/Info.plist;
				LD_RUNPATH_SEARCH_PATHS = (
					"$(inherited)",
					"@executable_path/../Frameworks",
				);
				PRODUCT_BUNDLE_IDENTIFIER = com.openrouter.tracker;
				PRODUCT_NAME = "$(TARGET_NAME)";
				SWIFT_VERSION = 5.0;
			}};
			name = Debug;
		}};
\t\t{app_cfg_release_id} /* Release */ = {{
			isa = XCBuildConfiguration;
			buildSettings = {{
				ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;
				CODE_SIGN_IDENTITY = "-";
				CODE_SIGN_STYLE = Manual;
				CODE_SIGN_ENTITLEMENTS = OpenRouterTrackerApp/OpenRouterTracker.entitlements;
				COMBINE_HIDPI_IMAGES = YES;
				GENERATE_INFOPLIST_FILE = NO;
				INFOPLIST_FILE = OpenRouterTrackerApp/Info.plist;
				LD_RUNPATH_SEARCH_PATHS = (
					"$(inherited)",
					"@executable_path/../Frameworks",
				);
				PRODUCT_BUNDLE_IDENTIFIER = com.openrouter.tracker;
				PRODUCT_NAME = "$(TARGET_NAME)";
				SWIFT_VERSION = 5.0;
			}};
			name = Release;
		}};
\t\t{widget_cfg_debug_id} /* Debug */ = {{
			isa = XCBuildConfiguration;
			buildSettings = {{
				CODE_SIGN_IDENTITY = "-";
				CODE_SIGN_STYLE = Manual;
				CODE_SIGN_ENTITLEMENTS = OpenRouterWidgetExtension/OpenRouterWidget.entitlements;
				GENERATE_INFOPLIST_FILE = NO;
				INFOPLIST_FILE = OpenRouterWidgetExtension/Info.plist;
				LD_RUNPATH_SEARCH_PATHS = (
					"$(inherited)",
					"@executable_path/../Frameworks",
					"@executable_path/../../../../Frameworks",
				);
				PRODUCT_BUNDLE_IDENTIFIER = com.openrouter.tracker.widget;
				PRODUCT_NAME = "$(TARGET_NAME)";
				SKIP_INSTALL = YES;
				SWIFT_VERSION = 5.0;
			}};
			name = Debug;
		}};
\t\t{widget_cfg_release_id} /* Release */ = {{
			isa = XCBuildConfiguration;
			buildSettings = {{
				CODE_SIGN_IDENTITY = "-";
				CODE_SIGN_STYLE = Manual;
				CODE_SIGN_ENTITLEMENTS = OpenRouterWidgetExtension/OpenRouterWidget.entitlements;
				GENERATE_INFOPLIST_FILE = NO;
				INFOPLIST_FILE = OpenRouterWidgetExtension/Info.plist;
				LD_RUNPATH_SEARCH_PATHS = (
					"$(inherited)",
					"@executable_path/../Frameworks",
					"@executable_path/../../../../Frameworks",
				);
				PRODUCT_BUNDLE_IDENTIFIER = com.openrouter.tracker.widget;
				PRODUCT_NAME = "$(TARGET_NAME)";
				SKIP_INSTALL = YES;
				SWIFT_VERSION = 5.0;
			}};
			name = Release;
		}};
/* End XCBuildConfiguration section */

/* Begin XCConfigurationList section */
\t\t{proj_cfg_list_id} /* Build configuration list for PBXProject "{proj_name}" */ = {{
			isa = XCConfigurationList;
			buildConfigurations = (
				{proj_cfg_debug_id} /* Debug */,
				{proj_cfg_release_id} /* Release */,
			);
			defaultConfigurationIsVisible = 0;
			defaultConfigurationName = Release;
		}};
\t\t{app_cfg_list_id} /* Build configuration list for PBXNativeTarget "{app_target_name}" */ = {{
			isa = XCConfigurationList;
			buildConfigurations = (
				{app_cfg_debug_id} /* Debug */,
				{app_cfg_release_id} /* Release */,
			);
			defaultConfigurationIsVisible = 0;
			defaultConfigurationName = Release;
		}};
\t\t{widget_cfg_list_id} /* Build configuration list for PBXNativeTarget "{widget_target_name}" */ = {{
			isa = XCConfigurationList;
			buildConfigurations = (
				{widget_cfg_debug_id} /* Debug */,
				{widget_cfg_release_id} /* Release */,
			);
			defaultConfigurationIsVisible = 0;
			defaultConfigurationName = Release;
		}};
/* End XCConfigurationList section */

	}};
	rootObject = {proj_id} /* Project object */;
}}
"""
    xcodeproj_dir = project_dir / f"{proj_name}.xcodeproj"
    xcodeproj_dir.mkdir(parents=True, exist_ok=True)
    pbxproj_path = xcodeproj_dir / "project.pbxproj"
    with open(pbxproj_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Generated {pbxproj_path}")


if __name__ == "__main__":
    generate_pbxproj(Path(__file__).resolve().parent)
