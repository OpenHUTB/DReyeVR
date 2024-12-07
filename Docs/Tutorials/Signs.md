# 在Carla世界中添加自定义指示牌

## 这是什么？
让实验参与者自然地知道要采取什么方向，而无需人工干预，这通常很有用。在 Carla 中这不是问题，因为所有驾驶员都是 AI 控制器，但对于人类来说，我们不能简单地获取表示路点和方向的文本文件。这就是环境中的方向标志可以发挥作用的地方。不幸的是，Carla 没有提供任何方向标志（因为这对他们来说不是问题），而且步骤足够多，值得提供指南，所以请看这里。

本指南将向您展示如何创建自己的自定义标志并将其放置在任何 Carla 关卡中（*从技术上讲，该指南可以在 Carla 中添加任何自定义道具，而不仅仅是标志*）
- 步骤如下：
  1. 创建标志纹理（rgb/normals）
  2. 创建标志网格 & 材质
  3. 将新的材质应用到蓝图上
  4. Manually place the blueprint into the world
  5. **Optional:** Register the new sign with the blueprint library

## 入门
Sign textures can be found in Carla in the `carla/Unreal/CarlaUE4/Content/Carla/Static/TrafficSign/` directory. 

For example, you should see a directory that looks like this:

![SignDirectory](../Figures/Signs/directory.jpg)

Notice how all the models have a corresponding directory (some are cut off in the screenshot). These are where the static meshes and textures are defined so they can be used on these sign-shaped blueprints. 

- For the rest of this guide, we'll focus on using the `NoTurn` directory that looks like this when opened in the content browser:
![NoTurnDir](../Figures/Signs/no_turn_dir.jpg)

- From left to right these are the **Material Instance** (`M_` prefix), **Static Mesh** (`SM_` prefix), **Texture RGB** (`__0` suffix), and **Texture Normals** (`_n` suffix)

## 第 1 步: 创建标志纹理
The "NO TURN" sign serves as a good baseline for creating our custom signs, though any signs can be used as a starting point. 

Now, you can screenshot the image (or find its source file in Details->File Path) to get a `.jpg` of the desired texture, then clear out the original text ("NO TURN") so it is a blank canvas. For your convenience we have a blank "NO TURN" sign already provided in [`Content/Static/DefaultSign.jpg`](../../Content/Static/DefaultSign.jpg)
- Notice how the bottom right corner of these images has is a small gray-ish region. This is actually for the rear of the sign so that when it is applied on to the models, the rear has this metallic surface. 
  - This means we want to do most of our sign content editing in the region within the black perimeter

It is useful to have a powerful image editing tool for this, we used [GIMP](https://www.gimp.org/) (free & open source) and the rest of this section will reference it as the image editing tool.

From within Gimp you should be able to add whatever static components you like (text, images, etc.) within the designated region. Once you are finished with your new sign image, export it as a `.jpg`.

Next, you'll want GIMP to create the normals map for you. This can be done easily by going through `Filters -> Generic -> Normal Map` and applying the default normal generation to the newly created image. Export this file with the suffix `_n.jpg` to indicate that it is the normal map.

For example, if we wanted our sign to say "RIGHT TO CITY A", then after this process you should see something that looks like this:

![SignTextures](../Figures/Signs/textures_no_turn.jpg)

Now we are done with image manipulation and using GIMP. 

Now back in UE4, it'll be easiest if you duplicate the `TrafficSign/NoTurn/` directory into your custom directory (such as `DReyeVR_Signs/` with all the same 4 elements (material, static mesh, texture RGB, and texture normals)).
- Note: there are some reports of users not being able to copy/paste/duplicate directly in the editor. In this case, just do so in your file manager and reopen the editor again.
  - ```bash
	cd $CARLA_ROOT/Unreal/CarlaUE4/Content/Carla/Static/TrafficSign/
	cp -r NoTurn/ RightCityA/
    ```
  - ```bash
	# now RightCityA contains the following
	RightCityA
	- M_NoTurns.uasset
	- SM_noTurn.uasset
	- SM_noTurn_n.uasset
	- SM_noTurn_.uasset
    ``` 

|                                                                                                                                                                                                                                                                              |                                                                    |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Now, in your new custom directory, you can easily reimport a new `.jpg` source file by clicking the `Reimport` button at the top. </br> </br> Locate your rgb `.jpg` image for the `SM_noTurn` reimport, and use the normals `.jpg` image for the `SM_noTurn_n` reimport. | <img src = "../Figures/Signs/reimport.jpg" alt="Reimport" width=150%> |

Feel free to rename the `SM_noTurn_*` asset files **within the editor** (right click in content browser -> rename) and keep the naming scheme. Something like `SM_RightCityA` and `SM_RightCityA_n`.

## 第 2 步: 创建标志网格 & 材质
Now, you should make sure that the **Material** (`M_noTurns`) asset file is updated with the new textures. This may occur automatically, but just in case you should open it up in the editor and select the newly created `SM_RightCityA` and `SM_RightCityA_n` as the Texture parameter values for `SpeedSign_d` and `SpeedSign_n` respectively.
- To do this, click the dropdown menu box which say `SM_noTurn` and `SM_noTurn_n` and search for the new `RightCityA` variants
- The parameters should then look something like this
	![Parameters](../Figures/Signs/parameters.jpg)

Save it and rename it (**in the editor**) as well: `M_RightCityA` should suffice.

Now, finally open up the `SM_noTurn_` (static mesh) asset file and ensure it uses our newly created `M_RightCityA` material by editing the Material element in the Material Slots:
- Similarly to before, this is done in the Details pane by clicking the dropdown, searching for "RightCity", and selecting our new material
	![SignMaterial](../Figures/Signs/material.jpg)

Save it and rename it (always **in the editor**): `SM_RightCityA_` works.

At this point you should have a `RightCityA` directory that looks like the following:

![RightCityDir](../Figures/Signs/rightcity_directory.jpg)

## 第 3 步: 将新的材质应用到蓝图上

Once all the desired materials/static meshes are ready, duplicate a sign blueprint (from the parent `TrafficSign` directory) and place it in `RightCityA`
- This should be doable from within the editor. Right click `BP_NoTurns` -> Duplicate -> Enter new name -> Drag to `RightCityA/` -> select move

Open up the blueprint to the `Viewport` tab and select the sign component (not the pole)

In the Details pane you should again see a `Static Mesh` component that is still the `SM_noTurn_`, replace that with out new `SM_RightCityA_` asset, Recompile & Save, and you should be done. 

Now it should look like this: 

![SignBP](../Figures/Signs/bp.jpg)

## 第 4 步: 将新标志放到世界中

With our new sign blueprint, we can place it into the world fairly easily. Simply drag and drop it into the world, then edit its transform, rotation, and scale parameters to fine tune the result. 

The end result should look pretty decent, here's an example of our new sign in `Town03`

| Front of the sign                           | Rear of the sign                          |
| ------------------------------------------- | ----------------------------------------- |
| ![FrontSign](../Figures/Signs/right_front.jpg) | ![RearSign](../Figures/Signs/right_rear.jpg) |

Notice how both the front and rear look good, this is because the rear is given the metallic region from the bottom-right of the texture. 

## 第 5 步: （可选）在蓝图库中注册

在 Carla 的蓝图库中注册我们的新标志使我们能够从 PythonAPI 生成标志，从而允许在运行时动态放置。

这比现有的 Carla 标志更深入一些，因为它们不是设计为动态生成的，而是在编译时静态地放置在世界中。如果我们想在地图周围放置不同的标志以适应各种场景，而无需重新编译所有内容，这会变得令人沮丧。

根据 [此问题](https://github.com/carla-simulator/carla/issues/4363) ，在 Carla 0.9.11 上使用自定义道具的常规方式目前已损坏且不可靠。我们找到了一种 [变通方法]([workaround](https://github.com/carla-simulator/carla/issues/4363#issuecomment-924140532)) 并将其包含在问题中。

本质上，您需要编辑 `carla/Unreal/CarlaUE4/Content/Carla/Config/Default.Package.json` 文件以包含您的新标志道具，如下所示：
```json
{
    "name": "YOUR_SIGN_NAME",
    "path": "/PATH/TO/YOUR/SM_SIGN.SM_SIGN",
    "size": "Medium"
}
```
Note that the `"path"` source is looking for a UE4 static mesh object, which will be stored as a `.uasset` file. Still denote it as `SM_name.SM_name` in the `json`. 

Importantly, if you want to include a custom prop directory in `Content/` (instead of using our `DReyeVR/DReyeVR_Signs/` content) you should add this to the list of cooked assets in `Config/DefaultGame.ini` such as:

```ini
+DirectoriesToAlwaysCook=(Path="/Game/DReyeVR/DReyeVR_Signs") # what we include
+DirectoriesToAlwaysCook=(Path="/Game/YOUR_PROP_DIR/") # any desired prop directory
```
This ensures your custom props are properly cooked during shipping (`make package`). 

Once this change is imported in the map you will be able to spawn your sign as follows:
```python
bp = blueprint_library.filter(("static.prop.YOUR_SIGN_NAME").lower()) # filter is lowercase!
assert len(bp) == 1 # you should only have one prop of this name
transform = world.get_map().get_spawn_points()[0] # or choose any other spawn point
world.spawn_actor(bp[0], transform) # should succeed with no errors
```

**NOTE** In constructing our (and Carla's) signs, we unlink the sign itself from the pole it connects to. Therefore, if you want to spawn the sign *with* the pole you'll need to combine these static meshes. 
- This is supported within the editor by placing both actors into the world, selecting both, then using the Window -> Developer -> MergeActors button as described in [this guide](https://docs.unrealengine.com/4.27/en-US/Basics/Actors/Merging/). 
- We have already provided a baseline with the [`Content/DReyeVR_Signs/FullSign/`](Content/DReyeVR_Signs/FullSign/) directory where we combined the signs with the poles as a single static mesh. 
	- With this baseline, assuming you have a compatible material (using the same sign template as ours) you can just update the material for the sign component without further modification. 


# 自动放置标志
使用我们的 [scenario-runner 分支](https://github.com/HARPLab/scenario_runner/tree/DReyeVR-0.9.13) 时，有逻辑可以根据路线特征（直行、左转、右转和目标）自动生成相应的方向标志。此逻辑可在 [route_scenario 的导航标志代码](https://github.com/HARPLab/scenario_runner/blob/3b5e60f15fd97de00332f80610051f9f39d7db8c/srunner/scenarios/route_scenario.py#L284-L355) 中找到。由于这会自动应用于所有路线，因此您可以通过注释 `self._setup_nav_signs(self.route)` 方法调用来手动禁用它。


如果您想要手动放置特定路线的标志，也可以使用文件方法（请参阅 [此处](https://github.com/HARPLab/scenario_runner/blob/DReyeVR-0.9.13/srunner/data/all_routes_signs.json) ），但我们发现自动放置标志在大多数情况下效果很好，而且更方便。因此建议使用自动方法，您无需执行任何操作即可启用它。
