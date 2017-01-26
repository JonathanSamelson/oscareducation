function validateExerciceController($scope, $http, $sce, $timeout, $location) {
    $scope.uploadFile = function(files) {
        var reader = new FileReader();
        reader.readAsDataURL(files[0]);
        reader.addEventListener("load", function() {
            console.log("yay")
            $scope.base64img = reader.result;
            $scope.$digest();
        })
    }

    $scope.validateExercice = function() {
        var content = $scope.yaml;
        $http.post("validate/", {"questions": $scope.questions, "testable_online": $scope.testable_online})
            .error(function() {
                console.log("error")
                $scope.yamlValidationResult = $sce.trustAsHtml('<div class="alert alert-danger">Une erreur s\'est produite, nous en avons été alerté.</div>');
            })
            .success(function(data) {
                console.log("success");
                if (data.yaml.result == "error") {
                    $scope.yamlValidationResult = $sce.trustAsHtml('<div class="alert alert-danger"> <b>Erreur:</b> ' + data.yaml.message + '</b></div>');
                    $scope.exerciceIsValid = false;
                } else {
                    $scope.yamlValidationResult = $sce.trustAsHtml('<div class="alert alert-success">' + data.yaml.message + '</b></div>');

                    $scope.yamlRendering = $sce.trustAsHtml(data.rendering);
                    $scope.htmlRendering = $sce.trustAsHtml($scope.html);

                    $timeout(function() {
                        $('#exercice-rendering-yaml input[type="submit"]').addClass("disabled");
                        MathJax.Hub.Typeset();
                    }, 0);

                    $scope.exerciceIsValid = true;
                }
            })

    }

    $scope.proposeToOscar = function() {
        var yaml = $scope.yaml;
        var html = $scope.html;
        var skill_code = $scope.skillCode;

        if (!skill_code) {
            $scope.yamlValidationResult = $sce.trustAsHtml('<div class="alert alert-danger"><b>Erreur :</b> vous devez sélectionner une compétence pour pouvoir proposer l\'exercice à Oscar.</div>');
            return;
        }

        $("#submit-pull-request").addClass("disabled");

        $http.post("submit/", {"questions": $scope.questions, "html": html, "skill_code": skill_code, "image": $scope.base64img, "testable_online": $scope.testable_online})
            .success(function(data) {
                if (inUpdateMode) {
                    window.location.href = "..";
                }

                $scope.yamlValidationResult = $sce.trustAsHtml('<div class="alert alert-success">L\'exercice a correctement été soumis, nous le validerons prochainement, un grand merci !');
                console.log(data);

                $scope.yaml = "";
                $scope.html = "";
                $scope.skillCode = "";
                $scope.image = null;
                $scope.base64img = "";
                $scope.exerciceIsValid = ""
                $scope.htmlRendering = ""
                $scope.yamlRendering = ""
                $scope.testable_online = true;

                $scope.questions = [{
                    "instructions": "",
                    "type": "",
                    "answers": [{
                        "text": "",
                        "latex": "",
                        "correct": false,
                    }],
                }]
            })
            .error(function() {
                $scope.yamlValidationResult = $sce.trustAsHtml('<div class="alert alert-danger">Une erreur s\'est produite, nous en avons été alerté.</div>');
            })
            .finally(function() {
                $timeout(function() {
                    $("#submit-pull-request").removeClass("disabled");
                }, 0);
            })
    }

    $scope.onChangeQuestionType = function(topIndex, question) {
        if (question.type.startsWith("math")) {
            $timeout(function() { $scope.renderMathquil(topIndex, question) }, 100);
        }
    }

    $scope.onChangeRadio = function(question, answer) {
        if (question.type != "radio")
            return;

        if (answer.correct !== true)
            return;

        for (a in question.answers) {
            var a = question.answers[a];
            if (a !== answer && a.correct === true) {
                a.correct = false;
            }
        }
    }

    $scope.addAnswer = function(topIndex, question) {
        question["answers"].push({
            "text": "",
            "correct": false,
        })

        if (question.type.startsWith("math")) {
            $timeout(function() { $scope.renderMathquil(topIndex, question) }, 100);
        }
    }

    $scope.removeAnswer = function(question, answer) {
        question["answers"].splice(question["answers"].indexOf(answer), 1);
    }

    $scope.addQuestion = function() {
        $scope.questions.push({
            "instructions": "",
            "type": "",
            "answers": [{
                "text": "",
                "correct": false,
            }],
        })
    }

    $scope.removeQuestion = function(question) {
        $scope.questions.splice($scope.questions.indexOf(question), 1);
    }

    var checkIfEditingExercice = function() {
        // this is a horrible hack to get to make this code works both for
        // create and edition of exercices :(
        let uri = window.location.href.split("/").filter(function(a) { return a }).slice(-1);

        if (uri[0] != "update") {
            console.log("New ercercice mode");
            return;
        }

        inUpdateMode = true;

        $http.get("json/").success(function(data) {
            $scope.skillCode = data.skillCode;
            $scope.html = data.html;
            $scope.yaml = data.yaml;
            $scope.questions = data.questions;

            // TODO yamlRendering/htmlRendering et image
            $timeout(function() {
                for (var i = 0; i < $scope.questions.length; ++i) {
                    if ($scope.questions[i].type.startsWith("math")) {
                        $scope.renderMathquil(i, $scope.questions[i])
                    }
                }
            }, 100);
        })
    }

    $scope.renderMathquil = function(topIndex, question) {
        console.log("renderMathquil, topIndex: " + topIndex);
        var MQ = MathQuill.getInterface(2);

        var specialKeys = {
            right: "Right",
            left: "Left",
            Down: "Down",
            Up: "Up",
            bksp: "Backspace",
            tab: "Tab"
        }

        // add special keys, but don't override previous keyaction definitions
        Object.keys(specialKeys).forEach(function(key){
            if (!$.keyboard.keyaction[key]) {
                $.keyboard.keyaction[key] = specialKeys[key];
            }
        });

        console.log($(".mathquill-" + topIndex));
        $(".mathquill-" + topIndex).each(function(index, mq) {
            var mathquill = MQ.MathField(mq, {
                handlers: {
                    edit: function() {
                        question.answers[index].latex = mathquill.latex();
                        console.log(question.answers[index].latex);
                    }
                }
            });

            if (question.answers[index].text) {
                mathquill.latex(question.answers[index].text);
            }

            var keyboard = $($(mq).parent().children()[0]);

            $(mq).click(function(){
                // keyboard.getkeyboard().reveal();
                keyboard.getkeyboard().reveal();
            })

            keyboard
                .on('keyboardChange', function(e, keyboard, el) {
                    console.log(e.action);
                    if (specialKeys[e.action]) {
                        mathquill.keystroke(specialKeys[e.action]);
                    } else if (e.action == "()") {
                        mathquill.cmd("(");
                        mathquill.cmd(")");
                        mathquill.keystroke("Left");
                    } else {
                        mathquill.cmd(e.action);
                    }
                    // $('#mathquill').focus();
                })
            .keyboard({
                usePreview: false,
                lockInput: true,
                noFocus: true,
                layout: 'custom',
                display: {
                    "Down": "&darr;",
                    "Up": "&uarr;"
                },
                customLayout: MATH_CUSTOM_LAYOUT[$(mq).attr("data-keyboard-type")],
                useCombos: false
            })
            // activate the typing extension
            .addTyping({
                showTyping: true,
                delay: 250
            });
        });
    }

    $scope.skillCode = $location.search().code;
    $scope.html = "";
    $scope.yaml = "";
    $scope.yamlRendering = "";
    $scope.htmlRendering = "";
    $scope.image = null;
    $scope.base64img = "";
    $scope.testable_online = true;

    var inUpdateMode = false;

    $scope.questions = [{
        instructions: "",
        type: "",
        answers: [{
            text: "",
            latex: "",
            correct: false,
        }],
    }]

    $scope.yamlValidationResult = "";
    $scope.exerciceIsValid = false;

    checkIfEditingExercice();
}
