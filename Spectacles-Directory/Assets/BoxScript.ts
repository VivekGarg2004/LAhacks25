@component
export class NewScript extends BaseScriptComponent {
    onAwake() {
        let boxObject = this.getSceneObject();

        let newScripComponent = boxObject.createComponent('ScriptComponent');

        let referenceScript = boxObject.getComponent('ScriptComponent');
    }
}
