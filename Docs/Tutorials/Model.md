# 修改车辆模型

您可能有兴趣为车辆网格本身添加新功能，而不仅仅是我们在 DReyeVR 中提供的功能。在本指南中，我们将帮助您熟悉一些工具和基本要求，以及我们如何修改原始 Carla Tesla 静态网格以拥有动态方向盘的示例。

请注意，为了继续，我们假设您可以访问以下软件：
- 虚幻引擎编辑器
- Carla (从源代码编译)
- Blender ([免费下载](https://www.blender.org/download/))

## 入门
如果您已经有了主意，那么首先要看的肯定是 Carla 自己关于 [添加自定义车辆](https://carla.readthedocs.io/en/latest/tuto_A_add_vehicle/) 的出色指南。但它仍然是一本不错的读物，可以帮助您了解实现可行的 CARLA/UE4 车辆的底层机制：
- [骨骼](https://docs.unrealengine.com/4.27/en-US/AnimatingObjects/SkeletalMeshAnimation/Persona/VirtualBones/): 骨骼可以被认为是一种索具(rigging)实体，可以使实体之间的连接变得刚性和受约束。
- [骨架](https://docs.unrealengine.com/4.26/en-US/AnimatingObjects/SkeletalMeshAnimation/Skeleton/): 骨架包含骨骼的位置和方向及其层次结构。 
- [物理网格](https://docs.unrealengine.com/4.26/en-US/InteractiveExperiences/Physics/PhysicsAssetEditor/): 表示网格重要特征周围的边界框。主要用于碰撞检测
- [动画](https://docs.unrealengine.com/4.27/en-US/AnimatingObjects/SkeletalMeshAnimation/AnimBlueprints/): 动画蓝图通常通过某些状态机逻辑来控制骨架网格的动画。
- [蓝图](https://docs.unrealengine.com/4.27/en-US/ProgrammingAndScripting/Blueprints/UserGuide/Types/ClassBlueprint/): 将以上所有内容组合成一个高度动态且灵活的 UObject，可作为我们的车辆代理。 

考虑到所有这些，您可能会对以下内容感兴趣：
- 蓝图: `$CARLA_ROOT/Unreal/CarlaUE4/Content/Carla/Blueprints/Vehicles/XYZ`
- 其他: `$CARLA_ROOT/Unreal/CarlaUE4/Content/Carla/Static/Vehicles/4Wheeled/XYZ`

# 示例：添加动态方向盘
问题：没有反应灵敏的方向盘驾驶起来非常不协调，而且由于 Carla 车辆网格不是为人类驾驶员设计的，因此没有必要将方向盘与整个车辆外壳分开。这很成问题，因为方向盘现在是车辆网格的一部分，无法在运行时进行动画处理。

在我们的例子中，我们选择使用 TeslaM3 网格作为我们的基类，因此我们也将在这里使用它。

我们的行动计划是：
1. 从车辆中提取方向盘网格并创建其自己的静态网格
2. 更新车辆网格以移除方向盘
3. 将方向盘重新连接为基于代码的动态对象

对于步骤 1 和 2，我们将使用免费开源的 Blender 程序进行 3D 建模工作：

## 1. 提取方向盘网格

### 导出到 FBX
首先，转到您想要导出的静态网格文件，在我们的例子中，我们想要导出 `$CARLA_ROOT/Unreal/CarlaUE4/Content/Carla/Static/Vehicles/4Wheeled/Tesla/SM_TeslaM3_v2.uasset`（请注意，这些文件应该有一个粉红色下划线，以表明它们是完整的静态网格文件）。

### 一个细节层次
我建议对这次导出使用最高的细节层次(LOD, [Level-Of-Detail](../../LODS.md) )设置，因为该车辆将始终靠近相机，因此拥有多个 LOD 是没有意义的，并且它使导入到 blender 变得更简单。

为此，只需双击进入静态网格，然后在左侧“资产详细信息(Asset Details)”窗格中的“LOD 设置(LOD Settings)”中将“LOD 数量(Number of LODs)”滑块向下拖动到 1，然后单击“应用更改(Apply Changes)”，如下所示。
- ![LODs](../Figures/Model/LOD1.jpg)

### 导出到 blender
现在，返回内容浏览器(`Content Browser`)，您可以右键单击该文件，然后选择 资产操作->导出(`Asset Actions -> Export`) 并指定要导出生成的 `.FBX` 文件的位置。
- ![Export](../Figures/Model/Export.jpg)

### 在 Blender 中建模
现在，打开一个新的 Blender 窗口并删除默认生成的立方体。然后转到 `File -> Import -> FBX (.fbx)`  并选择刚刚创建的文件。

现在你应该看到一个简单的 Blender 窗口，其中有这样的车辆：
- ![BlenderSolid](../Figures/Model/BlenderSolid.jpg)

要使用 `WASD` 控件切换移动，请按 `shift + ` `。移动到车内，您可以找到方向盘。

我发现，最有效提取方向盘的方法是使用线框模式选择所有顶点，即使是实体渲染中不可见的顶点。要进入线框模式，请按 `z` 键，然后选择线框 `wireframe`（应该是最左边的选项）。然后您应该会看到类似以下内容：
- ![WireframeWheel](../Figures/Model/WireframeWheel.jpg)

然后，为了实际选择正确的顶点，我们需要在视口的左上角从“对象模式`Object Mode`”更改为“编辑模式`Edit Mode`”。然后，我们需要以某种方式定位相机，以尽量减少选择不需要的顶点，并使用我们想要的任何选择技术（我喜欢套索lasso选择）来选择整个方向盘，如下所示：
- ![SelectedWheel](../Figures/Model/SelectedWheel.jpg)
注意：如果您选择了多余的顶点，您可以随时通过按住 `shift+click` 并单击单个顶点来撤消这些顶点。

然后，您应该能够将整个束移出车辆（或使用 `shift+d` 复制它们并清理原始内容），以获得如下所示的效果：
| Wireframe | Rendered |
| --- | --- |
| ![WireFrameGotWheel](../Figures/Model/WheelOut.jpg) | ![SolidOut](../Figures/Model/VehicleAndWheel.jpg) | 

最后，您应该能够导出单个选择（需要导出仅车轮和仅车辆模型），方法是以相同的方式（以线框形式）选择所有顶点并删除它们（然后当然撤消删除）。然后选择 `File -> Export -> FBX(.fbx)` 以获得最佳兼容性。对车辆网格和方向盘都执行此操作（导出时我将方向盘移到原点，但我不确定这是否必要）。


## 2. 更新车辆网格

### 返回编辑器
现在，回到编辑器中，我们将为车辆网格和方向盘创建一个新目录。本节中的大部分内容是 [Carla 提供的文档](https://carla.readthedocs.io/en/latest/tuto_A_add_vehicle/) 的修改版本。

然后，在新的 `Mesh` 目录中，我们可以简单地在内容浏览器中单击鼠标右键，然后选择“导入资产`Import Asset`”，然后选择我们的 FBX 模型。确保将“导入内容类型**Import Content Type**”设置为“几何和蒙皮权重`Geometry and Skinning Weights`”，将“法线导入方法**Normal Import Method**”设置为“导入法线`Import Normals`”，将“材质导入方法**Material Import Method**”设置为“不创建材质`Do not create materials`”，最后取消选中“导入纹理**Import Textures**”。

我们现在应该有一个（带下划线的粉色）骨架网格资源、（带下划线的米色）物理资产和（带下划线的淡蓝色）骨架资产。然后，右键单击新的（带下划线的粉色）骨架网格资产，并选择 `Create -> Anim Blueprint` 以创建新的动画蓝图。

在此动画蓝图中，请确保以下内容：
- 转到`Class settings -> Details -> Class Options -> Parent Class`，并将该类重新设置为 `VehicleAnimInstance`。
- 在`My Blueprint`部分中，单击`AnimGraph`并从现有的 `TeslaM3` 动画复制相同的图形逻辑，如下所示：

| 重定父级(Reparent)                                    | 动画                                           | 
|---------------------------------------------------|----------------------------------------------| 
| ![Reparent](../Figures/Model/AnimClassOption.jpg) | ![AnimGraph](../Figures/Model/AnimGraph.jpg) | 

现在您已经完成动画蓝图。

根据我的经验，我必须做一些额外的调整才能为我的整体网格（粉红色下划线）使用正确的组件，如下所示：
- `Asset Details -> Physics Asset`: Replace new with the existing `$CARLA_ROOT/Unreal/CarlaUE4/Content/Carla/Static/Vehicles/4Wheeled/Tesla/SM_TeslaM3_PhysicsAsset.uasset` physics asset (NOT the `_v2_` model!)
- `Asset Details -> Lighting`: Same as the Physics Asset
- `Preview Scene Settings -> Animation Blueprint`: The new animation blueprint you just created. 

Then finally, you can delete the newly imported PhysicsAsset file since it is no longer being used (I opted to use the vanilla TeslaM3 one instead)

And in `BP_EgoVehicle_DReyeVR`, you can finally edit the `Mesh (Inherited) -> Details -> Mesh` field to use the new SM we just updated (pink underline). Since this clears the `Animation` section, you'll also need to update the `Mesh (Inherited) -> Animation -> Anim Class` field to use the new animation class we just made. 

Now the DReyeVR EgoVehicle should be fully drivable and operates just as it did before, but now with no steering wheel in the driver's seat!
![NoWheel](../Figures/Model/NoWheel.jpg)

## 3. 动态重新连接方向盘
### Import to UE4
现在我们要将方向盘重新导入引擎，以便我们可以在运行时动态地生成、放置和更新它。

The easiest way to do this is through importing the SteeringWheel `.fbx` just like with the Vehicle mesh, from there it should have all the original textures pre-applied and be slightly angled. 

To get rotations of the wheel to be in the Roll axis of the wheel itself (not its attachment), I recommend slightly tilting the static mesh wheel so that it is mostly vertical and select `Make Static Mesh`. 

This will allow you to create a plain simple static mesh (cyan underline) from the skeletal mesh (pink underline) as follows:
| Rotated Skeletal Mesh | Resulting Directory | 
| --- | --- |
| ![RotWheel](../Figures/Model/WheelRot.jpg) | ![SelectedWheel](../Figures/Model/SelectSMWheel.jpg) |

### Import in code
Now that we have a reasonable steering wheel model as a simple static mesh, it is easy to spawn it and attach it to the ego-vehicle (currently without a steering wheel) in code. Managing it in code is nice because it will allow us to `SetRelativeRotation` of the mesh dynamically on every tick, allowing it to be responsive to our inputs at runtime. 

The first step to Spawn the steering wheel in code is to find its mesh in the editor. Right click on the static mesh (cyan underline) and select `Copy Reference`. For me it looks like this:
- `"StaticMesh'/Game/DReyeVR/EgoVehicle/TeslaM3/SteeringWheel/Wheel_StaticMeshl_model3.Wheel_StaticMeshl_model3'"`

(Note that we won't be needing any of the other steering wheel assets anymore, feel free to delete them)

在代码中添加 Unreal 组件的一般策略是在构造函数中生成它们，然后使用它们的引用以及它们的 C++ API。对于我们的情况，我们只需要一个构造函数和一个 tick 方法（参见 [EgoVehicle::ConstructSteeringWheel & EgoVehicle::TickSteeringWheel](../../DReyeVR/EgoVehicle.cpp) ）

Now enjoy a responsive steering wheel asset attached to the EgoVehicle as you drive around!