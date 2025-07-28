/*
    Winwheel.js, by Douglas McKechie @ www.dougtesting.net
    See website for tutorials and examples.

    This file is greatly simplified to contain just the functionality required to draw a wheel.
    It is not the full Winwheel.js code which is available from www.dougtesting.net
*/

class Winwheel
{
    // Priavte properties.
    #canvas;
    #ctx;
    #centerX;
    #centerY;
    #outerRadius;
    #innerRadius;
    #numSegments;
    #segments;
    #drawMode;
    #rotationAngle;
    #textFontFamily;
    #textFontSize;
    #textFontWeight;
    #textOrientation;
    #textAlignment;
    #textDirection;
    #textMargin;
    #textFillStyle;
    #textStrokeStyle;
    #textLineWidth;
    #fillStyle;
    #strokeStyle;
    #lineWidth;
    #clearTheCanvas;
    #imageOverlay;
    #drawText;
    #pointerAngle;
    #wheelImage;
    #imageDirection;
    #responsive;

    #animation;
    #pin;
    #pins;
    #pointerGuide;

    #tween;

    // Some sensible defaults.
    constructor(options, drawWheel)
    {
        // Add default values for the params.
        this.#canvas = null;
        this.#ctx = null;
        this.#centerX = (options.centerX !== undefined) ? options.centerX : null;
        this.#centerY = (options.centerY !== undefined) ? options.centerY : null;
        this.#outerRadius = (options.outerRadius !== undefined) ? options.outerRadius : null;
        this.#innerRadius = (options.innerRadius !== undefined) ? options.innerRadius : 0;
        this.#numSegments = (options.numSegments !== undefined) ? options.numSegments : 0;
        this.#segments = (options.segments !== undefined) ? options.segments : null;
        this.#drawMode = (options.drawMode !== undefined) ? options.drawMode : 'code';
        this.#rotationAngle = (options.rotationAngle !== undefined) ? options.rotationAngle : 0;
        this.#textFontFamily = (options.textFontFamily !== undefined) ? options.textFontFamily : 'Arial';
        this.#textFontSize = (options.textFontSize !== undefined) ? options.textFontSize : 20;
        this.#textFontWeight = (options.textFontWeight !== undefined) ? options.textFontWeight : 'normal';
        this.#textOrientation = (options.textOrientation !== undefined) ? options.textOrientation : 'horizontal';
        this.#textAlignment = (options.textAlignment !== undefined) ? options.textAlignment : 'center';
        this.#textDirection = (options.textDirection !== undefined) ? options.textDirection : 'normal';
        this.#textMargin = (options.textMargin !== undefined) ? options.textMargin : null;
        this.#textFillStyle = (options.textFillStyle !== undefined) ? options.textFillStyle : 'black';
        this.#textStrokeStyle = (options.textStrokeStyle !== undefined) ? options.textStrokeStyle : null;
        this.#textLineWidth = (options.textLineWidth !== undefined) ? options.textLineWidth : 1;
        this.#fillStyle = (options.fillStyle !== undefined) ? options.fillStyle : 'silver';
        this.#strokeStyle = (options.strokeStyle !== undefined) ? options.strokeStyle : 'black';
        this.#lineWidth = (options.lineWidth !== undefined) ? options.lineWidth : 1;
        this.#clearTheCanvas = (options.clearTheCanvas !== undefined) ? options.clearTheCanvas : true;
        this.#imageOverlay = (options.imageOverlay !== undefined) ? options.imageOverlay : false;
        this.#drawText = (options.drawText !== undefined) ? options.drawText : true;
        this.#pointerAngle = (options.pointerAngle !== undefined) ? options.pointerAngle : 0;
        this.#wheelImage = (options.wheelImage !== undefined) ? options.wheelImage : null;
        this.#imageDirection = (options.imageDirection !== undefined) ? options.imageDirection : 'N';
        this.#responsive = (options.responsive !== undefined) ? options.responsive : false;

        this.#animation = (options.animation !== undefined) ? options.animation : null;
        this.#pin = (options.pin !== undefined) ? options.pin : null;
        this.#pins = (options.pins !== undefined) ? options.pins : null;
        this.#pointerGuide = (options.pointerGuide !== undefined) ? options.pointerGuide : null;

        // The tween object used to animate the wheel.
        this.#tween = null;

        // If the id of the canvas is set then get a reference to it.
        if (options.canvasId) {
            // Get the canvas context.
            this.#canvas = document.getElementById(options.canvasId);

            if (this.#canvas) {
                // If the centerX and centerY have not been specified in the options then default to center of the canvas
                // and make the outerRadius half of the canvas width - this means the wheel will fill the canvas.
                if (this.#centerX === null) {
                    this.#centerX = this.#canvas.width / 2;
                }

                if (this.#centerY === null) {
                    this.#centerY = this.#canvas.height / 2;
                }

                if (this.#outerRadius === null) {
                    // Use smallest of the canvas width or height as the basis for the radius.
                    if (this.#canvas.width < this.#canvas.height) {
                        this.#outerRadius = (this.#canvas.width / 2) - this.#lineWidth;
                    } else {
                        this.#outerRadius = (this.#canvas.height / 2) - this.#lineWidth;
                    }
                }

                // Get the canvas context.
                this.#ctx = this.#canvas.getContext('2d');
            } else {
                this.#canvas = null;
                this.#ctx = null;
            }
        }

        // Pop all the options in to the properties of this object.
        for (let key in options) {
           if (this[key] !== undefined) {
               this[key] = options[key];
           }
        }

        // If the segments have been specified then create a segmet object for each.
        if (this.#segments !== null) {
            // Check that the number of segments is not more than the number of items in the segments array.
            if (this.#numSegments > this.#segments.length) {
                this.#numSegments = this.#segments.length;
            }
        } else {
            this.#numSegments = 0;
        }

        // If the drawWheel parameter is true then call the draw method to render the wheel straight away.
        if (drawWheel) {
            this.draw();
        } else if (this.#drawMode === 'image') {
            // If drawing an image then need to trigger the draw, otherwise happens after the image has loaded.
            // But don't call draw until the wheel object has been initialised.
            this.draw();
        }

        if (this.#responsive) {
            this.#canvas.style.width = '100%';

            // Create a debounced version of the draw function.
            let debouncedDraw = this.debounce(this.draw, 500);

            let resizeObserver = new ResizeObserver(entries => {
                debouncedDraw();
            });

            resizeObserver.observe(this.#canvas.parentElement);
        }
    }

    // ====================================================================================================================
    // This function is called when the wheel is to be animated.
    // ====================================================================================================================
    startAnimation()
    {
        // Make sure animation properties have been set.
        if (this.#animation) {
            // Call function to compute the animation properties.
            this.computeAnimation();

            // Start the animation.
            if (this.#tween) {
                this.#tween.start();
            }
        }
    }

    // ====================================================================================================================
    // This function computes the animation values - the distance in degrees to spin, the duration, the easing function
    // and setups the callbacks.
    // ====================================================================================================================
    computeAnimation()
    {
        // Set the animation properties.
        if (this.#animation) {
            // Set the spin to property.
            if (this.#animation.type === 'spinToStop') {
                // The angle the wheel has to spin which is some number of complete spins plus the angle to the target.
                this.#animation.propertyValue = (this.#animation.spins * 360) + this.#animation.stopAngle;
            }

            // If the duration is not set, calculate it using the default spin time.
            if (!this.#animation.duration) {
                this.#animation.duration = 5;
            }
        }

        // Set the callbacks.
        let callbacks = {
            onUpdate : this.draw.bind(this),
            onComplete : this.animationComplete.bind(this)
        };

        // Do the tweening.
        this.#tween = gsap.to(this, {
            duration: this.#animation.duration,
            rotationAngle: this.#animation.propertyValue,
            ease: this.#animation.easing || "power3.inOut",
            onUpdate: callbacks.onUpdate,
            onComplete: callbacks.onComplete
        });
    }

    // ====================================================================================================================
    // Called when the animation has finished.
    // ====================================================================================================================
    animationComplete()
    {
        // If the callback has been specified, call it.
        if (this.#animation.callbackFinished) {
            eval(this.#animation.callbackFinished + '(' + 'this.getIndicatedSegment()' + ')');
        }
    }

    // ====================================================================================================================
    // This function returns the segment the pointer is currently over.
    // ====================================================================================================================
    getIndicatedSegment()
    {
        // Call function to return the segment number over.
        let prizeNumber = this.getSegmentNumberAt(this.#pointerAngle);

        // Get the actual segment object from the segments array.
        let indicatedSegment = this.#segments[prizeNumber - 1];

        // Undefined is returned if the prizeNumber is not in the segments array.
        return indicatedSegment;
    }

    // = an==================================================================================================================
    // This function returns the segment number that the specified angle is over (0-360).
    // ====================================================================================================================
    getSegmentNumberAt(angle)
    {
        let anglePercent = this.getAnglePercent(angle);
        let prizePercent = 0;
        let i;
        let segmentNumber;

        // Find the segment that the angle is in.
        for (i=0; i<this.#segments.length; i++) {
            // Add the percent of this segment to the total percent, then check if the angle is in this prize.
            prizePercent += this.#segments[i].size / 360 * 100;

            if (anglePercent <= prizePercent) {
                segmentNumber = i;
                break;
            }
        }

        // The segment number is the loop iterator + 1.
        return (segmentNumber + 1);
    }

    // ====================================================================================================================
    // This function coverts a value in degrees to a percent of the wheel.
    // ====================================================================================================================
    getAnglePercent(angle)
    {
        // Get the current rotation of the wheel - this will be in the range 0-360.
        let currentRotation = this.getCurrentAngle();

        // We need to add this to the specified angle to get the position of the angle on the wheel.
        let angleOnWheel = angle + currentRotation;

        // Now we need to normalise this to 0-360.
        let normalisedAngle = this.normaliseAngle(angleOnWheel);

        // Then we can work out the percent.
        let anglePercent = (normalisedAngle / 360) * 100;

        return anglePercent;
    }

    // ====================================================================================================================
    // This function returns the current angle of rotation of the wheel in the range 0-360.
    // ====================================================================================================================
    getCurrentAngle()
    {
        // The rotation angle will be in the range 0-360.
        return this.normaliseAngle(this.#rotationAngle);
    }

    // ====================================================================================================================
    // This function normalises an angle to 0-360.
    // ====================================================================================================================
    normaliseAngle(angle)
    {
        let remainder = angle % 360;

        return remainder;
    }

    // ====================================================================================================================
    // This function draws the wheel on the canvas.
    // ====================================================================================================================
    draw(clearTheCanvas)
    {
        // Can't draw if have no canvas context.
        if (this.#ctx) {
            // Clear the canvas if required.
            if ((clearTheCanvas !== undefined && clearTheCanvas === true) || this.#clearTheCanvas === true) {
                this.#ctx.clearRect(0, 0, this.#canvas.width, this.#canvas.height);
            }

            // If a wheel image is specified, and it has loaded then draw the image.
            if (this.#drawMode === 'image') {
                // If the wheel image has loaded.
                if (this.#wheelImage && this.#wheelImage.width) {
                    // Draw the wheel image on the canvas.
                    this.drawWheelImage();
                } else {
                    // If the wheel image has not loaded then call function to load it first.
                    this.loadWheelImage();
                }

                // If the text is to be rendered on top of the image then draw it after the image.
                if (this.#drawText === true) {
                    this.drawSegmentText();
                }

                if (this.#imageOverlay === true) {
                    // This is not working as expected.
                    // this.drawSegments();
                }
            } else { // code draw mode.
                // Draw the segments.
                this.drawSegments();

                // If the text is to be drawn, do it.
                if (this.#drawText === true) {
                    this.drawSegmentText();
                }
            }

            // If this.#pins is true, draw the pins.
            if (this.#pins === true || (typeof this.#pins === 'object' && this.#pins !== null)) {
                // If the pins are to be drawn, do it.
                this.drawPins();
            }

            // If a pointer guide is defined, draw it.
            if (this.#pointerGuide) {
                this.drawPointerGuide();
            }
        }
    }

    // ====================================================================================================================
    // This function draws the segments of the wheel.
    // ====================================================================================================================
    drawSegments()
    {
        // Can't draw if have no canvas context.
        if (this.#ctx) {
            // Set the variable that will be used to track the angle of the segments.
            let lastAngle = this.#rotationAngle;
            let segment;

            // Loop through all the segments and draw them.
            for (let x = 1; x <= this.#numSegments; x ++) {
                // Get the segment object.
                segment = this.#segments[x-1];

                // Set the fill style and stroke style for the segment.
                if (segment.fillStyle !== undefined) {
                    this.#ctx.fillStyle = segment.fillStyle;
                } else {
                    this.#ctx.fillStyle = this.#fillStyle;
                }

                if (segment.strokeStyle !== undefined) {
                    this.#ctx.strokeStyle = segment.strokeStyle;
                } else {
                    this.#ctx.strokeStyle = this.#strokeStyle;
                }

                if (segment.lineWidth !== undefined) {
                    this.#ctx.lineWidth = segment.lineWidth;
                } else {
                    this.#ctx.lineWidth = this.#lineWidth;
                }

                // Beging a path as the segment is a type of shape.
                this.#ctx.beginPath();

                // If the inner radius is set then draw an arc segment.
                if (this.#innerRadius) {
                    // A line from the center to the start of the segment on the outer radius.
                    this.#ctx.moveTo(this.#centerX, this.#centerY);
                }

                // Draw the outer arc of the segment.
                this.#ctx.arc(this.#centerX, this.#centerY, this.#outerRadius, this.degToRad(lastAngle), this.degToRad(lastAngle + segment.size));

                if (this.#innerRadius) {
                    // If the inner radius is set, draw another arc to the center of the wheel to make a donut shape.
                    this.#ctx.arc(this.#centerX, this.#centerY, this.#innerRadius, this.degToRad(lastAngle + segment.size), this.degToRad(lastAngle), true);
                } else {
                    // If the inner radius is not set, draw a line to the center of the wheel to make a pie shape.
                    this.#ctx.lineTo(this.#centerX, this.#centerY);
                }

                // Fill and stroke the segment.
                this.#ctx.fill();
                this.#ctx.stroke();

                // Increment the last angle used for the next segment.
                lastAngle += segment.size;
            }
        }
    }

    // ====================================================================================================================
    // This function draws the text on the segments.
    // ====================================================================================================================
    drawSegmentText()
    {
        // Can't draw if have no canvas context.
        if (this.#ctx) {
            let lastAngle = this.#rotationAngle;
            let segment;
            let text;

            // Loop through all the segments and draw the text on them.
            for (let x = 1; x <= this.#numSegments; x ++) {
                // Get the segment object.
                segment = this.#segments[x-1];
                text = segment.text;

                // Set the fill style and stroke style for the text.
                if (segment.textFillStyle !== undefined) {
                    this.#ctx.fillStyle = segment.textFillStyle;
                } else {
                    this.#ctx.fillStyle = this.#textFillStyle;
                }

                if (segment.textStrokeStyle !== undefined) {
                    this.#ctx.strokeStyle = segment.textStrokeStyle;
                } else {
                    this.#ctx.strokeStyle = this.#textStrokeStyle;
                }

                if (segment.textLineWidth !== undefined) {
                    this.#ctx.lineWidth = segment.textLineWidth;
                } else {
                    this.#ctx.lineWidth = this.#textLineWidth;
                }

                // Set the font for the text.
                this.#ctx.font = (segment.textFontWeight ? segment.textFontWeight + ' ' : this.#textFontWeight + ' ') +
                               (segment.textFontSize ? segment.textFontSize : this.#textFontSize) + 'px ' +
                               (segment.textFontFamily ? segment.textFontFamily : this.#textFontFamily);

                // If the text is not null or undefined then draw it.
                if (text) {
                    // Depending on the text orientation, draw the text in different ways.
                    if (segment.textOrientation === 'curved') {
                        this.drawCurvedText(text, lastAngle, segment.size);
                    } else if (segment.textOrientation === 'vertical') {
                        this.drawVerticalText(text, lastAngle, segment.size);
                    } else { // horizontal.
                        this.drawHorizontalText(text, lastAngle, segment.size);
                    }
                }

                // Increment the last angle used for the next segment.
                lastAngle += segment.size;
            }
        }
    }

    // ====================================================================================================================
    // This function draws the text horizontally on the segments.
    // ====================================================================================================================
    drawHorizontalText(text, lastAngle, size)
    {
        // Save the context so we can restore it after we are done.
        this.#ctx.save();

        // The angle of the text is the center of the segment.
        let angle = lastAngle + (size / 2);

        // Move the context to the center of the wheel.
        this.#ctx.translate(this.#centerX, this.#centerY);

        // Rotate the context to the angle of the segment.
        this.#ctx.rotate(this.degToRad(angle));

        // Move the context to the position of the text.
        let textX = 0;
        let textY = 0;

        // If the text margin is set then move the context to that distance from the center.
        if (this.#textMargin) {
            textX = this.#textMargin;
        } else {
            // Move the context to the center of the segment.
            textX = (this.#outerRadius - this.#innerRadius) / 2 + this.#innerRadius;
        }

        // Set the text alignment.
        this.#ctx.textAlign = this.#textAlignment;

        // Set the text baseline.
        this.#ctx.textBaseline = 'middle';

        // Flip the text if it is to be drawn in reverse.
        if (this.#textDirection === 'reversed') {
            this.#ctx.scale(-1, -1);
        }

        // Fill and stroke the text.
        this.#ctx.fillText(text, textX, textY);
        this.#ctx.strokeText(text, textX, textY);

        // Restore the context.
        this.#ctx.restore();
    }

    // ====================================================================================================================
    // This function draws the text vertically on the segments.
    // ====================================================================================================================
    drawVerticalText(text, lastAngle, size)
    {
        // Save the context so we can restore it after we are done.
        this.#ctx.save();

        // The angle of the text is the center of the segment.
        let angle = lastAngle + (size / 2);

        // Move the context to the center of the wheel.
        this.#ctx.translate(this.#centerX, this.#centerY);

        // Rotate the context to the angle of the segment.
        this.#ctx.rotate(this.degToRad(angle));

        // Set the text alignment.
        this.#ctx.textAlign = this.#textAlignment;

        // Set the text baseline.
        this.#ctx.textBaseline = 'middle';

        // Move the context to the position of the text.
        let textX = 0;
        let textY = 0;

        // If the text margin is set then move the context to that distance from the center.
        if (this.#textMargin) {
            textY = this.#textMargin;
        } else {
            // Move the context to the center of the segment.
            textY = (this.#outerRadius - this.#innerRadius) / 2 + this.#innerRadius;
        }

        // Flip the text if it is to be drawn in reverse.
        if (this.#textDirection === 'reversed') {
            this.#ctx.scale(-1, -1);
        }

        // Fill and stroke the text.
        this.#ctx.fillText(text, textX, textY);
        this.#ctx.strokeText(text, textX, textY);

        // Restore the context.
        this.#ctx.restore();
    }

    // ====================================================================================================================
    // This function draws the text along the curve of the segments.
    // ====================================================================================================================
    drawCurvedText(text, lastAngle, size)
    {
        // Save the context so we can restore it after we are done.
        this.#ctx.save();

        // The angle of the text is the center of the segment.
        let angle = lastAngle + (size / 2);

        // Move the context to the center of the wheel.
        this.#ctx.translate(this.#centerX, this.#centerY);

        // Set the text alignment.
        this.#ctx.textAlign = this.#textAlignment;

        // Set the text baseline.
        this.#ctx.textBaseline = 'middle';

        // The radius of the text is the center of the segment.
        let textRadius = (this.#outerRadius - this.#innerRadius) / 2 + this.#innerRadius;

        // If the text margin is set then use that as the radius.
        if (this.#textMargin) {
            textRadius = this.#textMargin;
        }

        // The angle of the text is the center of the segment.
        let textAngle = this.degToRad(angle);

        // If the text is to be drawn in reverse then reverse the angle.
        if (this.#textDirection === 'reversed') {
            textAngle = this.degToRad(angle + 180);
        }

        // Rotate the context to the angle of the text.
        this.#ctx.rotate(textAngle);

        // The text is drawn from the center of the wheel, so we need to move the context to the position of the text.
        this.#ctx.translate(textRadius, 0);

        // The text is drawn along the curve of the segment, so we need to rotate each character.
        let characterAngle = 0;
        let character;
        let characterWidth;
        let characterRotation;
        let characterX;
        let characterY;

        // Loop through all the characters in the text.
        for (let i = 0; i < text.length; i++) {
            // Get the character.
            character = text.charAt(i);

            // Get the width of the character.
            characterWidth = this.#ctx.measureText(character).width;

            // The rotation of the character is the width of the character divided by the radius of the text.
            characterRotation = characterWidth / textRadius;

            // The x and y position of the character is the center of the character.
            characterX = 0;
            characterY = 0;

            // The text alignment is set to center, so we need to move the context to the left by half the width of the character.
            if (this.#textAlignment === 'center') {
                characterX = -characterWidth / 2;
            }

            // The text baseline is set to middle, so we need to move the context up by half the height of the character.
            // There is no easy way to get the height of the character, so we just use the font size.
            if (this.#ctx.textBaseline === 'middle') {
                characterY = -this.#textFontSize / 2;
            }

            // Fill and stroke the character.
            this.#ctx.fillText(character, characterX, characterY);
            this.#ctx.strokeText(character, characterX, characterY);

            // Rotate the context for the next character.
            this.#ctx.rotate(characterRotation);
        }

        // Restore the context.
        this.#ctx.restore();
    }

    // ====================================================================================================================
    // This function draws the pins on the wheel.
    // ====================================================================================================================
    drawPins()
    {
        // Can't draw if have no canvas context.
        if (this.#ctx) {
            // Set the fill style and stroke style for the pins.
            if (this.#pins.fillStyle !== undefined) {
                this.#ctx.fillStyle = this.#pins.fillStyle;
            } else {
                this.#ctx.fillStyle = this.#fillStyle;
            }

            if (this.#pins.strokeStyle !== undefined) {
                this.#ctx.strokeStyle = this.#pins.strokeStyle;
            } else {
                this.#ctx.strokeStyle = this.#strokeStyle;
            }

            if (this.#pins.lineWidth !== undefined) {
                this.#ctx.lineWidth = this.#pins.lineWidth;
            } else {
                this.#ctx.lineWidth = this.#lineWidth;
            }

            // The number of pins is the number of segments.
            let numPins = this.#numSegments;

            // If the number of pins is specified in the options then use that.
            if (this.#pins.number !== undefined) {
                numPins = this.#pins.number;
            }

            // The angle between the pins is 360 divided by the number of pins.
            let angleBetweenPins = 360 / numPins;
            let pinAngle;

            // The radius of the pins is the outer radius of the wheel minus the margin of the pins.
            let pinRadius = this.#outerRadius;

            // If the margin is specified in the options then subtract it from the radius.
            if (this.#pins.margin !== undefined) {
                pinRadius -= this.#pins.margin;
            }

            // If the outer radius of the pins is specified in the options then use that as the radius of the pins.
            if (this.#pins.outerRadius !== undefined) {
                // Not the radius of the pin, the radius of the circle the pins are on.
                // pinRadius = this.#pins.outerRadius;
            }

            // Loop through all the pins and draw them.
            for (let i = 1; i <= numPins; i++) {
                // The angle of the pin is the angle between the pins multiplied by the pin number.
                pinAngle = i * angleBetweenPins;

                // Save the context so we can restore it after we are done.
                this.#ctx.save();

                // Move the context to the center of the wheel.
                this.#ctx.translate(this.#centerX, this.#centerY);

                // Rotate the context to the angle of the pin.
                this.#ctx.rotate(this.degToRad(pinAngle + this.#rotationAngle));

                // Move the context to the position of the pin.
                this.#ctx.translate(pinRadius, 0);

                // Draw the pin as a circle.
                this.#ctx.beginPath();
                this.#ctx.arc(0, 0, this.#pins.outerRadius, 0, 2 * Math.PI);
                this.#ctx.fill();
                this.#ctx.stroke();

                // Restore the context.
                this.#ctx.restore();
            }
        }
    }

    // ====================================================================================================================
    // This function draws the pointer guide on the wheel.
    // ====================================================================================================================
    drawPointerGuide()
    {
        // Can't draw if have no canvas context.
        if (this.#ctx) {
            // Save the context so we can restore it after we are done.
            this.#ctx.save();

            // Move the context to the center of the wheel.
            this.#ctx.translate(this.#centerX, this.#centerY);

            // Rotate the context to the angle of the pointer.
            this.#ctx.rotate(this.degToRad(this.#pointerAngle));

            // Set the fill style and stroke style for the pointer guide.
            if (this.#pointerGuide.fillStyle !== undefined) {
                this.#ctx.fillStyle = this.#pointerGuide.fillStyle;
            } else {
                this.#ctx.fillStyle = this.#fillStyle;
            }

            if (this.#pointerGuide.strokeStyle !== undefined) {
                this.#ctx.strokeStyle = this.#pointerGuide.strokeStyle;
            } else {
                this.#ctx.strokeStyle = this.#strokeStyle;
            }

            if (this.#pointerGuide.lineWidth !== undefined) {
                this.#ctx.lineWidth = this.#pointerGuide.lineWidth;
            } else {
                this.#ctx.lineWidth = this.#lineWidth;
            }

            // Draw the pointer guide as a line.
            this.#ctx.beginPath();
            this.#ctx.moveTo(this.#innerRadius, 0);
            this.#ctx.lineTo(this.#outerRadius, 0);
            this.#ctx.stroke();

            // Restore the context.
            this.#ctx.restore();
        }
    }

    // ====================================================================================================================
    // This function draws the wheel image on the canvas.
    // ====================================================================================================================
    drawWheelImage()
    {
        // Can't draw if have no canvas context.
        if (this.#ctx) {
            // Save the context so we can restore it after we are done.
            this.#ctx.save();

            // Move the context to the center of the wheel.
            this.#ctx.translate(this.#centerX, this.#centerY);

            // Rotate the context to the angle of the wheel.
            this.#ctx.rotate(this.degToRad(this.#rotationAngle));

            // The image is drawn from the center of the wheel, so we need to move the context to the top left of the image.
            this.#ctx.translate(-this.#wheelImage.width / 2, -this.#wheelImage.height / 2);

            // Draw the image.
            this.#ctx.drawImage(this.#wheelImage, 0, 0);

            // Restore the context.
            this.#ctx.restore();
        }
    }

    // ====================================================================================================================
    // This function loads the wheel image.
    // ====================================================================================================================
    loadWheelImage()
    {
        // Can't draw if have no canvas context.
        if (this.#ctx) {
            // Create a new image object.
            this.#wheelImage = new Image();

            // Set the onload function of the image.
            this.#wheelImage.onload = () => {
                // When the image has loaded, draw the wheel.
                this.draw();
            };

            // Set the src of the image.
            this.#wheelImage.src = this.#wheelImage;
        }
    }

    // ====================================================================================================================
    // This function converts degrees to radians.
    // ====================================================================================================================
    degToRad(d)
    {
        return d * 0.0174532925199432957;
    }

    // ====================================================================================================================
    // This function will create a debounced version of a function.
    // ====================================================================================================================
    debounce(func, wait, immediate)
    {
        let timeout;

        return function executedFunction() {
            const context = this;
            const args = arguments;

            const later = function() {
              timeout = null;
              if (!immediate) func.apply(context, args);
            };

            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(context, args);
        };
    };
} 