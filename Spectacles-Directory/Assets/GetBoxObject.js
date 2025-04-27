// Gets SceneObject attached
var boxObj = script.getSceneObject();
// Creates a new ScriptComponent
var newScriptComp = boxObj.createComponent('ScriptComponent');

// Gets the ScriptComponent attached to the SceneObject
var mySceneObj = boxObj.getComponent('ScriptComponent');